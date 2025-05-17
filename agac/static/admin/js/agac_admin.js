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

    // Form submit öncesi kontrol
    document.querySelector('form').addEventListener('submit', function(e) {
        const rows = document.querySelectorAll('.urun-row');
        if (rows.length === 0) {
            e.preventDefault();
            alert('En az bir ürün eklemelisiniz!');
            return false;
        }

        // Ürünleri topla ve hidden input'a ekle
        const urunler = [];
        rows.forEach(row => {
            const urunId = row.getAttribute('data-urun-id');
            const miktar = row.querySelector('.agac-adet-input').value;
            
            if (parseInt(miktar) < 0) {
                e.preventDefault();
                alert('Ağaç adedi 0\'dan küçük olamaz!');
                return false;
            }

            urunler.push({
                urun_id: parseInt(urunId),
                miktar: parseInt(miktar)
            });
        });

        document.getElementById('agacUrunlerData').value = JSON.stringify(urunler);
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
        alert('Bu ürün zaten eklenmiş!');
        return;
    }

    const urunId = select.value;
    const urunAdi = selectedOption.text.split(' - ')[0];
    const stokAdet = selectedOption.getAttribute('data-stok');

    const tbody = document.getElementById('agacUrunlerBody');
    const row = document.createElement('tr');
    row.className = 'urun-row';
    row.setAttribute('data-urun-id', urunId);
    
    row.innerHTML = `
        <td style="padding: 8px; border: 1px solid #ddd;">${urunId}</td>
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
    closeUrunSecPopup();
}

function removeUrunRow(button) {
    if (confirm('Bu ürünü silmek istediğinizden emin misiniz?')) {
        const tbody = document.getElementById('agacUrunlerBody');
        const row = button.closest('tr');
        tbody.removeChild(row);
    }
} 