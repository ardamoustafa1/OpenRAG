# Operational Runbook

## Bölüm 1 — Günlük Operasyon Kontrol Listesi
Her sabah mesai başlangıcında SRE veya DevOps mühendisi tarafından kontrol edilmelidir:
- [ ] Grafana dashboard'larında kırmızı alert var mı?
- [ ] Celery queue derinliği < 50 mi?
- [ ] GPU belleği < %80 mi?
- [ ] Son 24 saatin hata oranı < %1 mi?
- [ ] Storage (MinIO, Postgres, Qdrant) disk kullanımı < %70 mi?
- [ ] Velero yedekleri (gece 02:00) başarıyla tamamlandı mı?

## Bölüm 2 — Yaygın Sorunlar ve Çözümler

### SORUN 1: LLM yanıtları çok yavaş (>30s)
**NEDEN:** GPU VRAM belleği dolu, vLLM/Ollama modeli swap (RAM'e diske yazma) yapıyor.
**ÇÖZÜM:** En çok bellek kullanan pod'u bul, `ollama ps` ile model listele ve kullanılmayan hafif/eski modelleri kaldır.
**KOMUT:**
```bash
kubectl top pods -n ai-platform
kubectl exec -it ollama-pod -n ai-platform -- ollama rm qwen2.5-72b
```

### SORUN 2: Celery queue doldu, dokümanlar işlenmiyor
**NEDEN:** Worker sayısı yetersiz (yüksek yük) veya bir task zombi (takılı) durumda.
**ÇÖZÜM:** Flower UI (Admin paneli) üzerinden takılı task'ları `revoke` et. Sonrasında HPA üzerinden Worker sayısını manuel artır.
**KOMUT:**
```bash
kubectl scale deployment ai-platform-celery-worker -n ai-platform --replicas=5
```

### SORUN 3: Qdrant bağlantı hatası (Timeout/503)
**NEDEN:** Qdrant pod'u OOMKilled (Out of Memory) yedi ve yeniden başladı. Koleksiyonların RAM'e geri yüklenmesi sürüyor.
**ÇÖZÜM:** Pod'un hazır olmasını bekle ve `ready` endpoint'ini kontrol et. Gerekirse Memory Limit değerini yükselt.
**KOMUT:**
```bash
kubectl get pods -l app.kubernetes.io/name=qdrant -n ai-platform -w
```

### SORUN 4: Tenant verisi görünmüyor (Row-Level Security Sorunu)
**NEDEN:** Veritabanına istek atılırken `SET app.current_tenant_id` değişkeni doğru bağlanmamış.
**ÇÖZÜM:** Backend loglarında `current_setting` hatalarını ara. Yetkilendirme middleware'inin (Token'dan Tenant ID çekme) düzgün çalıştığını doğrula.
**KOMUT:**
```bash
kubectl logs deployment/ai-platform-backend -n ai-platform | grep "current_setting"
```

### SORUN 5: SSO login çalışmıyor
**NEDEN:** OIDC/SAML metadata konfigürasyonu değişti veya sertifika (IdP) süresi doldu.
**ÇÖZÜM:** Traefik loglarını ve `auth` endpoint'ini kontrol et. SSO sağlayıcısının metadata URL'ini manuel ziyaret ederek SSL geçerliliğini onayla.
