# Disaster Recovery Plan (DRP)

**RTO (Recovery Time Objective):** < 4 saat  
**RPO (Recovery Point Objective):** < 1 saat (PostgreSQL WAL arşivleme ile)

## Senaryo 1: Tek Pod Başarısızlığı
- **Açıklama:** Uygulama (Backend, Celery vb.) kod kaynaklı veya OOMKilled nedeniyle çöker.
- **Otomatik Yanıt:** Kubernetes Liveness/Readiness probları sayesinde pod'u izole eder ve otomatik yeniden başlatır. 
- **Beklenen Kurtarma:** < 2 Dakika. İnsan müdahalesi gerekmez.

## Senaryo 2: Node (Fiziksel/Sanal Sunucu) Başarısızlığı
- **Açıklama:** K8s Cluster içerisindeki bir makine tamamen kapanır (Donanım arızası).
- **Otomatik Yanıt:** Pod'lar, Cluster içerisindeki sağlıklı Node'lara "Reschedule" (yeniden zamanlama) edilir. PodDisruptionBudget (PDB) kuralları gereği her zaman minimum 1 replica başka node'da ayaktadır.
- **Beklenen Kurtarma:** < 5 Dakika. 

## Senaryo 3: Tam Cluster Kaybı (Major Felaket)
**Süreç Adımları (Manuel Müdahale Gerektirir):**
1. **Cluster'ı Yeniden Oluştur (0-60 dk):** Terraform / IaC kullanarak bulut ortamında boş bir K8s Cluster ayağa kaldırın.
2. **Velero Restorasyonu (1-2 saat):** S3 üzerindeki yedeklerden tüm namespace ve diskleri (PVC) geri yükleyin:
   ```bash
   velero restore create --from-backup daily-backup --wait
   ```
3. **Veritabanı Point-In-Time-Recovery (30 dk):** Postgres verilerini saniyeler seviyesinde kurtarmak için WAL loglarını uygulayın.
4. **Qdrant Snapshot:** Vektör DB'yi restore edin.
5. **DNS Yönlendirmesi (15 dk):** Load Balancer IP'sini güncelleyin.
**Toplam RTO tahmini:** 3-4 saat.

## Senaryo 4: Veri Bozulması (Data Corruption)
- **Açıklama:** Uygulama hatası nedeniyle bir tablo veya vektör verisi geri alınamaz şekilde bozulmuştur.
- **Çözüm:** WAL arşivlerinden sadece ilgili bozuk tablonun yedeği çekilir, PostgreSQL'de ayrı bir isimle yaratılır. Bozuk kayıtlar `UPDATE/DELETE` ile düzeltilip Qdrant ile senkronizasyonu doğrulanır.

## Yıllık DR Tatbikatı (Game Day)
Müşteri uyumluluk standartları gereği her 6 ayda bir "Chaos Engineering" uygulanmalıdır. Bir staging ortamı silinerek baştan aşağı Velero ile ayağa kaldırılma süreci test edilir ve süreler raporlanır.
