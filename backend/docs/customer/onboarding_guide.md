# Kurumsal AI Platformu — Müşteri Başlangıç Rehberi

Kurumsal AI platformumuza hoş geldiniz! Bu rehber, şirketinize özel izole edilmiş sisteminize ilk adımları atmanızı sağlayacaktır. Platform, yüklediğiniz gizli şirket belgelerini okuyarak size yapay zeka destekli akıllı yanıtlar üretir. Verileriniz %100 güvendedir ve asla başka müşterilerle veya genel yapay zeka modellerinin eğitimiyle paylaşılmaz.

## Bölüm 1 — İlk Giriş (5 Dakika)
1. Şirketinize özel URL'ye gidin (Örn: `https://firma-adi.ai-platform.com`).
2. Yönetici (Admin) e-posta adresinize gelen davet bağlantısına tıklayın.
3. Yeni şifrenizi belirleyin. Güvenliğiniz için hesabınızı oluşturduktan hemen sonra Ayarlar menüsünden **Çift Aşamalı Doğrulama (MFA)** kurulumunu yapmanızı şiddetle tavsiye ederiz.

## Bölüm 2 — İlk Doküman Koleksiyonu (15 Dakika)
Yapay zekanın size cevap verebilmesi için öncelikle şirket belgelerinizi yüklemelisiniz.
1. Sol menüden **Koleksiyonlar (Collections)** sekmesine tıklayın.
2. Sağ üstteki **Yeni Koleksiyon** butonuna basın (Örn: "İnsan Kaynakları Politikaları").
3. Koleksiyon detayına girin ve şirketinize ait PDF, DOCX veya TXT dosyalarını ekrana sürükleyip bırakın.
4. Dosyaların yanındaki durum ikonunun `İşleniyor`'dan `Tamamlandı`'ya dönmesini bekleyin. Artık sistem belgelerinizi öğrendi!

## Bölüm 3 — Kullanıcı Davet Etme
1. **Yönetim > Kullanıcılar** sekmesine gidin.
2. Ekibinizdeki kişilerin e-posta adreslerini girip onlara **Editor** (Belge yükleyebilen) veya **Viewer** (Sadece soru sorabilen) rolü atayın.

## Bölüm 4 — AI'ya Soru Sorma (En İyi Pratikler)
- **Chat (Sohbet)** ekranına gidin.
- Soru sormadan önce yan panelden az önce oluşturduğunuz "Koleksiyonu" seçtiğinize emin olun.
- "Şirketin uzaktan çalışma politikası nedir?" gibi sorular sorun.
- Gelen cevabın hemen altında, yapay zekanın bu bilgiyi hangi sayfa ve belgeden aldığını gösteren **Kaynaklar (Citations)** butonlarını göreceksiniz. Kaynağı kontrol etmeyi unutmayın.

## Bölüm 5 — SSO Kurulumu (IT Ekibiniz İçin)
Eğer şirketiniz Azure AD, Google Workspace veya Okta kullanıyorsa, çalışanlarınızın ayrıca şifre belirlemesine gerek yoktur. IT ekibiniz, **Ayarlar > Güvenlik (SSO)** menüsündeki metadata URL'lerini kullanarak SAML 2.0 veya OpenID Connect entegrasyonunu saniyeler içinde tamamlayabilir.
