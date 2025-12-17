document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const exportBtn = document.getElementById('export-btn');

    // Drag and Drop Logic
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.style.background = '#eff6ff'; });
    dropZone.addEventListener('dragleave', () => dropZone.style.background = 'transparent');
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.background = 'transparent';
        if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) uploadFile(fileInput.files[0]);
    });

    exportBtn.addEventListener('click', () => {
        window.location.href = '/api/export';
    });
});

function formatRupiah(number) {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR' }).format(number);
}

async function loadDashboard() {
    try {
        const res = await fetch('/api/dashboard');
        const data = await res.json();

        document.getElementById('month-total').textContent = formatRupiah(data.monthly_total);
        
        if (data.highest_item) {
            document.getElementById('max-item-name').textContent = data.highest_item.product_name;
            document.getElementById('max-item-price').textContent = formatRupiah(data.highest_item.unit_price);
        }

        const list = document.getElementById('receipt-list');
        list.innerHTML = '';
        data.recent_receipts.forEach(r => {
            const li = document.createElement('li');
            li.innerHTML = `<span>${r.merchant || 'Unknown Merchant'} (${r.date})</span> <strong>${formatRupiah(r.total_amount)}</strong>`;
            list.appendChild(li);
        });
    } catch (err) {
        console.error("Error loading dashboard", err);
    }
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const loading = document.getElementById('loading');
    const dropZone = document.getElementById('drop-zone');
    
    dropZone.classList.add('hidden');
    loading.classList.remove('hidden');

    try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await res.json();
        
        if (res.ok) {
            displayReceiptDetails(data.receipt);
            loadDashboard(); // Refresh stats
        } else {
            alert('Error: ' + data.error);
        }
    } catch (err) {
        alert('Upload failed.');
        console.error(err);
    } finally {
        loading.classList.add('hidden');
        dropZone.classList.remove('hidden');
    }
}

function displayReceiptDetails(receipt) {
    const container = document.getElementById('scan-details');
    let html = `<h3>${receipt.merchant || 'Parsed Receipt'}</h3>`;
    html += `<table class="item-table"><thead><tr><th>Item</th><th class="text-right">Price</th></tr></thead><tbody>`;
    
    receipt.items.forEach(item => {
        html += `<tr><td>${item.product_name}</td><td class="text-right">${formatRupiah(item.subtotal)}</td></tr>`;
    });
    
    html += `<tr><td><strong>Total</strong></td><td class="text-right"><strong>${formatRupiah(receipt.total_amount)}</strong></td></tr>`;
    html += `</tbody></table>`;
    
    container.innerHTML = html;
}