document.addEventListener('DOMContentLoaded', function() {
    // Select2'yi başlat
    if (document.getElementById('urunSelect')) {
        $('#urunSelect').select2({
            dropdownParent: $('#urunSecPopup'),
            placeholder: "Ürün ara...",
            allowClear: false,
            minimumInputLength: 0,
            width: '100%'
        });
    }

    // Ağaç adedi değişikliklerini izle
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('agac-adet-input')) {
            const row = e.target.closest('tr');
            const urunId = row.getAttribute('data-urun-id');
            const yeniAdet = parseInt(e.target.value);
            
            if (yeniAdet < 0) {
                alert('Ağaç adedi 0\'dan küçük olamaz!');
                e.target.value = 0;
                return;
            }

            updateAgacUrunu(urunId, yeniAdet);
        }
    });

    // Form submit öncesi kontrol
    document.querySelector('form').addEventListener('submit', function(e) {
        e.preventDefault(); // Form submit'i engelle

        const rows = document.querySelectorAll('.urun-row');
        if (rows.length === 0) {
            alert('En az bir ürün eklemelisiniz!');
            return false;
        }

        // Tüm form verilerini topla
        const formData = {
            ad: document.getElementById('agacAdi').value,
            aciklama: document.getElementById('agacAciklama').value,
            urunler: []
        };

        // Tüm ürünleri topla
        rows.forEach(row => {
            const urunId = row.getAttribute('data-urun-id');
            const miktar = row.querySelector('.agac-adet-input').value;
            
            if (parseInt(miktar) < 0) {
                alert('Ağaç adedi 0\'dan küçük olamaz!');
                return false;
            }

            formData.urunler.push({
                urun_id: parseInt(urunId),
                miktar: parseInt(miktar)
            });
        });

        // Form verilerini gönder
        const agacId = window.location.pathname.split('/')[4];
        fetch(`/agac/duzenle/${agacId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Başarı mesajını göster
                const successMessage = document.createElement('div');
                successMessage.className = 'alert alert-success';
                successMessage.style.position = 'fixed';
                successMessage.style.top = '20px';
                successMessage.style.right = '20px';
                successMessage.style.zIndex = '1000';
                successMessage.innerHTML = data.message;
                document.body.appendChild(successMessage);

                // 3 saniye sonra mesajı kaldır
                setTimeout(() => {
                    successMessage.remove();
                    // Yönlendirme yap
                    window.location.href = data.redirect;
                }, 2000);
            } else {
                alert('Hata: ' + data.message);
            }
        })
        .catch(error => {
            alert('Bir hata oluştu: ' + error.message);
        });
    });
});

function showUrunSecPopup() {
    document.getElementById('urunSecPopup').style.display = 'block';
    $('#urunSelect').val(null).trigger('change');
}

function closeUrunSecPopup() {
    document.getElementById('urunSecPopup').style.display = 'none';
}

function addSelectedUrun() {
    const select = document.getElementById('urunSelect');
    const selectedOption = select.options[select.selectedIndex];
    
    if (!select.value) {
        alert('Lütfen bir ürün seçin!');
        return;
    }

    // Ürünün zaten eklenip eklenmediğini kontrol et
    const existingRow = document.querySelector(`.urun-row[data-urun-id="${select.value}"]`);
    if (existingRow) {
        // Eğer ürün zaten ekliyse, popup'ı kapat ve o ürünün adet inputuna focuslan
        closeUrunSecPopup();
        const adetInput = existingRow.querySelector('.agac-adet-input');
        if (adetInput) {
            adetInput.focus();
            adetInput.select(); // Mevcut değeri seç
        }
        return;
    }

    const urunId = parseInt(select.value); // ID'yi integer'a çevir
    const urunBilgileri = selectedOption.text.split(' - ');
    const urunKodu = urunBilgileri[0]; // UMY-603 formatındaki kodu al
    const urunAdi = urunBilgileri[1]; // Ürün adını al
    const stokAdet = selectedOption.getAttribute('data-stok');

    const tbody = document.getElementById('agacUrunlerBody');
    const row = document.createElement('tr');
    row.className = 'urun-row';
    row.setAttribute('data-urun-id', urunId);
    
    row.innerHTML = `
        <td style="padding: 8px; border: 1px solid #ddd;">${urunKodu}</td>
        <td style="padding: 8px; border: 1px solid #ddd;">${urunAdi}</td>
        <td style="padding: 8px; border: 1px solid #ddd;">${stokAdet}</td>
        <td style="padding: 8px; border: 1px solid #ddd;">
            <input type="number" class="agac-adet-input" value="1" min="0" required
                   style="width: 80px; padding: 4px;">
        </td>
        <td style="padding: 8px; border: 1px solid #ddd;">
            <button type="button" class="button" onclick="removeUrunRow(this)">
                <i class="fas fa-trash"></i> Sil
            </button>
        </td>
    `;

    tbody.appendChild(row);
    
    // Yeni ürünü veritabanına ekle
    updateAgacUrunu(urunId, 1);
    
    closeUrunSecPopup();
}

function removeUrunRow(button) {
    if (confirm('Bu ürünü silmek istediğinizden emin misiniz?')) {
        const row = button.closest('tr');
        const urunId = row.getAttribute('data-urun-id');
        
        // Ürünü veritabanından sil
        updateAgacUrunu(urunId, null).then(() => {
            const tbody = document.getElementById('agacUrunlerBody');
            tbody.removeChild(row);
        });
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function updateAgacUrunu(urunId, miktar) {
    const agacId = window.location.pathname.split('/')[4]; // URL'den ağaç ID'sini al
    const row = document.querySelector(`tr[data-urun-id="${urunId}"]`);
    
    try {
        // Loading durumunu göster
        if (row) {
            row.style.opacity = '0.5';
        }

        const response = await fetch(`/agac/update-urun/${agacId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                urun_id: parseInt(urunId),
                miktar: miktar
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Bir hata oluştu');
        }

        // UI'ı güncelle
        if (row) {
            if (miktar === null) {
                // Ürün silindiyse satırı kaldır
                row.remove();
            } else {
                // Ürün güncellendiyse opacity'yi geri al
                row.style.opacity = '1';
                
                // Adet inputunu güncelle
                const adetInput = row.querySelector('.agac-adet-input');
                if (adetInput) {
                    adetInput.value = miktar;
                }
            }
        }

        // Üretilebilir adedi güncelle
        calculateUretilebilirAdet();
        
        // Başarı mesajını göster
        const successMessage = document.createElement('div');
        successMessage.className = 'alert alert-success';
        successMessage.style.position = 'fixed';
        successMessage.style.top = '20px';
        successMessage.style.right = '20px';
        successMessage.style.zIndex = '1000';
        successMessage.innerHTML = data.message;
        document.body.appendChild(successMessage);
        
        // 3 saniye sonra mesajı kaldır
        setTimeout(() => {
            successMessage.remove();
        }, 3000);
        
    } catch (error) {
        // Hata durumunda opacity'yi geri al
        if (row) {
            row.style.opacity = '1';
        }
        
        // Hata mesajını göster
        const errorMessage = document.createElement('div');
        errorMessage.className = 'alert alert-danger';
        errorMessage.style.position = 'fixed';
        errorMessage.style.top = '20px';
        errorMessage.style.right = '20px';
        errorMessage.style.zIndex = '1000';
        errorMessage.innerHTML = 'Hata: ' + error.message;
        document.body.appendChild(errorMessage);
        
        // 3 saniye sonra mesajı kaldır
        setTimeout(() => {
            errorMessage.remove();
        }, 3000);
    }
} 