// Dashboard State
let allProducts = [];
let currentCategory = 'Groceries';
let allCustomers = [];
let pieChartInstance = null;
let lineChartInstance = null;
let cartSession = null;

// Initialization

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardStats();
    loadNotifications();
    loadShopStatus();
    setInterval(loadNotifications, 30000);

    // Close notifications if clicking outside
    document.addEventListener('click', () => {
        const dropdown = document.getElementById('notifDropdown');
        if (dropdown) dropdown.classList.remove('active');
    });
});

// Navigation
function switchTab(tabId) {
    // 1. Update Sidebar Active State
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(item => {
        if (item.getAttribute('onclick')?.includes(`'${tabId}'`)) {
            item.classList.add('active');
        }
    });

    // 2. Switch Content Panes (CRITICAL FIX)
    document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
    const targetTab = document.getElementById(`tab-${tabId}`);
    if (targetTab) targetTab.classList.add('active');

    // 3. Load Specific Data
    if (tabId === 'dashboard') loadDashboardStats();
    if (tabId === 'inventory') loadProducts();
    if (tabId === 'bills') loadBills();
    if (tabId === 'payments') loadPayments();
    if (tabId === 'customers') loadCustomersView();
    if (tabId === 'issues') loadCustomerIssues();
}

async function loadCustomerIssues() {
    const data = await api('/api/agent/admin/all-tickets');
    if (!data) return;

    const tbody = document.getElementById('issuesTableBody');
    tbody.innerHTML = data.tickets.length ? '' : '<tr><td colspan="6" style="text-align:center;">No issues found.</td></tr>';

    data.tickets.forEach(t => {
        const date = new Date(t.created_at).toLocaleDateString();
        const categoryBadge = t.category === 'Billing' ? 
            '<span class="badge badge-danger"><i class="fas fa-file-invoice-dollar"></i> Billing</span>' : 
            '<span class="badge badge-warning"><i class="fas fa-headset"></i> Support</span>';
        
        const statusBadge = t.status === 'Open' ? 
            `<span class="badge badge-warning">${t.status}</span>` : 
            `<span class="badge badge-success">${t.status}</span>`;

        tbody.innerHTML += `
            <tr>
                <td>${categoryBadge}</td>
                <td><strong>${t.customer_name}</strong></td>
                <td>
                    <div style="font-weight:600;">${t.title}</div>
                    <div style="font-size:0.75rem; color:var(--text-dim); max-width: 300px;">${t.description}</div>
                </td>
                <td>${statusBadge}</td>
                <td>${date}</td>
                <td>
                    ${t.status === 'Open' ? 
                        `<button class="btn btn-primary btn-sm" onclick='openResolveModal(${JSON.stringify(t)})'>Resolve</button>` : 
                        `<button class="btn btn-outline btn-sm" disabled>Resolved</button>`
                    }
                </td>
            </tr>
        `;
    });
}

function openResolveModal(ticket) {
    const content = document.getElementById('ticketDetailContent');
    content.innerHTML = `
        <div style="margin-bottom: 0.5rem;"><strong>From:</strong> ${ticket.customer_name}</div>
        <div style="margin-bottom: 0.5rem;"><strong>Title:</strong> ${ticket.title}</div>
        <div style="margin-bottom: 0.5rem;"><strong>Category:</strong> ${ticket.category}</div>
        <div style="border-top: 1px solid var(--border); padding-top: 0.5rem; margin-top: 0.5rem;">
            <strong>Description:</strong><br>${ticket.description}
        </div>
    `;
    document.getElementById('resolveTicketModal').dataset.ticketId = ticket.id;
    document.getElementById('resolutionMsg').value = '';
    
    openModal('resolveTicketModal');
}

async function confirmResolveTicket() {
    const ticketId = document.getElementById('resolveTicketModal').dataset.ticketId;
    const message = document.getElementById('resolutionMsg').value.trim();
    
    if (!message) return showToast("Please provide a resolution message", "warning");

    // Close IMMEDIATELY for better UX
    closeModal('resolveTicketModal');

    const res = await api('/api/agent/admin/resolve-ticket', 'POST', { ticket_id: ticketId, message });
    if (res) {
        showToast("Ticket resolved successfully!");
        // Clear
        document.getElementById('resolutionMsg').value = '';
        document.getElementById('resolveTicketModal').dataset.ticketId = '';
        loadCustomerIssues();
    } else {
        // If it failed, show it again
        openModal('resolveTicketModal');
    }
}

// Stats & Charts
async function loadDashboardStats() {
    const data = await api('/api/billing/dashboard_stats');
    if (!data) return;

    // Update Counters
    document.getElementById('stat-revenue').innerText = `₹${data.revenue.toFixed(2)}`;
    document.getElementById('stat-pending').innerText = data.pending_bills;
    document.getElementById('stat-lowstock').innerText = data.low_stock;
    document.getElementById('stat-customers').innerText = data.customers_count;

    // Render Charts
    renderPieChart(data.sales_data);
    renderLineChart(data.sales_trend);

    // Render Low Stock Table
    renderLowStockTable(data.low_stock_list);

    // Render Recent Alerts
    renderAlertList(data.alerts);

    // Load AI Predictions
    loadMLPredictions();
}

async function loadMLPredictions() {
    const list = document.getElementById('mlPredictionsList');
    if (!list) return;

    const data = await api('/api/ml/predictions');
    if (!data || !data.predictions || data.predictions.length === 0) {
        list.innerHTML = '<div class="text-dim" style="font-size:0.8rem; padding: 1rem;">No predictions available. Model might need more training data.</div>';
        return;
    }

    list.innerHTML = data.predictions.map(p => `
        <div class="ml-prediction-item ${p.status === 'High Demand' ? 'high-demand' : ''}">
            <div class="ml-pred-info">
                <h4>${p.product_name}</h4>
                <p>Status: <span style="color:${p.status === 'High Demand' ? 'var(--primary)' : 'var(--success)'}; font-weight:600;">${p.status}</span></p>
            </div>
            <div class="ml-pred-val">
                <span class="val">${p.predicted_demand}</span>
                <span class="label">Exp. Demand (${p.unit})</span>
            </div>
        </div>
    `).join('');
}

function renderPieChart(data) {
    const canvas = document.getElementById('salesPieChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (pieChartInstance) pieChartInstance.destroy();

    const labels = data.map(d => d.category);
    const values = data.map(d => d.sales);
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444'];

    pieChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: { labels, datasets: [{ data: values, backgroundColor: colors, borderWidth: 2, borderColor: '#fff' }] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 12, padding: 20, font: { family: 'Inter' } } }
            },
            cutout: '70%'
        }
    });
}

function renderLineChart(trendData) {
    const canvas = document.getElementById('salesLineChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (lineChartInstance) lineChartInstance.destroy();

    const labels = trendData.map(d => d.date);
    const values = trendData.map(d => d.total);

    lineChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Daily Revenue',
                data: values,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#3b82f6',
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, grid: { borderDash: [5, 5] } },
                x: { grid: { display: false } }
            },
            plugins: { legend: { display: false } }
        }
    });
}

function renderLowStockTable(list) {
    const tbody = document.getElementById('lowStockTableBody');
    if (!tbody) return;
    if (list.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center py-2">Inventory looks healthy!</td></tr>';
        return;
    }
    tbody.innerHTML = list.map(p => `
        <tr>
            <td><strong>${p.name}</strong></td>
            <td><span class="text-danger">${p.stock} pcs</span></td>
            <td>${p.threshold} pcs</td>
            <td><span class="badge ${p.status === 'Critical' ? 'badge-danger' : 'badge-warning'}">${p.status}</span></td>
        </tr>
    `).join('');
}

function renderAlertList(alerts) {
    const container = document.getElementById('recentAlertsList');
    if (!container) return;
    if (alerts.length === 0) {
        container.innerHTML = '<p class="text-dim text-center">No recent alerts</p>';
        return;
    }
    container.innerHTML = alerts.map(a => `
        <div class="alert-item ${a.title.includes('Low') ? 'danger' : 'warning'}">
            <div class="alert-item-icon">
                <i class="fas ${a.title.includes('Low') ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            </div>
            <div class="alert-item-content">
                <h4>${a.title}</h4>
                <p>${a.message}</p>
                <div class="alert-item-time">${formatRelativeTime(a.time)}</div>
            </div>
        </div>
    `).join('');
}

function formatRelativeTime(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diff = (now - date) / 1000;
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return date.toLocaleDateString();
}

// Notifications
function toggleNotifications(e) {
    if (e) e.stopPropagation();
    const dropdown = document.getElementById('notifDropdown');
    dropdown.classList.toggle('active');
    if (dropdown.classList.contains('active')) loadNotifications();
}

async function loadNotifications() {
    const data = await api('/api/notifications/all', 'GET', null, true);
    if (!data) return;

    const list = document.getElementById('notifList');
    const badge = document.getElementById('notifBadge');

    const unreadCount = data.notifications.filter(n => !n.is_read).length;
    if (unreadCount > 0) {
        badge.innerText = unreadCount;
        badge.classList.add('active');
    } else {
        badge.classList.remove('active');
    }

    if (data.notifications.length === 0) {
        list.innerHTML = '<div style="padding: 2rem; text-align: center; color: var(--text-dim); font-size: 0.85rem;">No new notifications</div>';
        return;
    }

    list.innerHTML = data.notifications.map(n => {
        const notifData = JSON.stringify(n).replace(/"/g, '&quot;');
        return `
            <div class="notif-item ${!n.is_read ? 'unread' : ''}" onclick="handleNotifClick(${notifData}, event)">
                <div class="notif-item-title">
                    ${!n.is_read ? '<div class="unread-dot"></div>' : ''}
                    <span>${n.title}</span>
                </div>
                <div class="notif-item-msg">${n.message}</div>
                <div class="notif-item-time">${formatRelativeTime(n.created_at)}</div>
            </div>
        `;
    }).join('');
}

async function handleNotifClick(notif, e) {
    if (e) e.stopPropagation();
    if (!notif.is_read) await api(`/api/notifications/mark-read/${notif.id}`, 'POST');

    if (notif.title === 'New Registration') switchTab('customers');
    else if (notif.title === 'Low Stock Alert') switchTab('inventory');

    document.getElementById('notifDropdown').classList.remove('active');
    loadNotifications();
}

async function markAllAsRead() {
    await api('/api/notifications/mark-all-read', 'POST');
    loadNotifications();
}

// Inventory & POS
async function loadProducts() {
    const data = await api('/api/inventory/products');
    if (!data) return;
    allProducts = data.products;
    renderProducts();
}

function filterCategory(cat) {
    currentCategory = cat;
    document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    renderProducts();
}

function renderProducts() {
    const grid = document.getElementById('productsGrid');
    if (!grid) return;
    grid.innerHTML = '';
    const filtered = currentCategory ? allProducts.filter(p => p.category === currentCategory) : allProducts;

    filtered.forEach(p => {
        const imgUrl = p.image_url || 'https://via.placeholder.com/250x150?text=No+Image';
        let actionBtn = `<button class="btn btn-sm btn-primary" style="flex:1;" onclick="editProduct(${p.id})">Edit</button>`;

        if (cartSession) {
            actionBtn = `<button class="btn btn-sm btn-success" style="flex:1;" onclick="addToCart(${p.id})">Add to Cart</button>`;
        }

        grid.innerHTML += `
            <div class="product-card ${p.stock <= p.low_stock_threshold ? 'low-stock' : ''}">
                <img src="${imgUrl}" class="product-img" alt="${p.name}">
                <div class="product-info">
                    <div class="flex-between">
                        <span class="product-name" style="font-weight:600;">${p.name}</span>
                        <span class="product-price" style="color:var(--success); font-weight:700;">₹${p.price}</span>
                    </div>
                    <div class="product-meta" style="font-size:0.8rem; color:var(--text-dim); margin: 0.5rem 0;">Stock: ${p.stock} ${p.unit} | ${p.category}</div>
                    <div class="product-actions" style="display:flex; gap:0.5rem;">
                        ${actionBtn}
                        ${!cartSession ? `<button class="btn btn-sm btn-danger" onclick="deleteProduct(${p.id})"><i class="fas fa-trash"></i></button>` : ''}
                    </div>
                </div>
            </div>
        `;
    });
}

// Modal Helpers
function openModal(id) { 
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('active');
        modal.style.setProperty('display', 'flex', 'important');
        modal.style.visibility = 'visible';
        modal.style.opacity = '1';
    }
}

function closeModal(id) { 
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('active');
        modal.style.setProperty('display', 'none', 'important');
        modal.style.visibility = 'hidden';
        modal.style.opacity = '0';
    }
}

// CRUD
function openAddProductModal() {
    document.getElementById('productForm').reset();
    document.getElementById('prodId').value = '';
    document.getElementById('prodImageUrl').value = '';
    document.getElementById('productModalTitle').innerText = 'Add Product';
    openModal('productModal');
}

async function editProduct(id) {
    const p = allProducts.find(x => x.id === id);
    if (!p) return;
    document.getElementById('prodId').value = p.id;
    document.getElementById('prodName').value = p.name;
    document.getElementById('prodCategory').value = p.category || 'Other';
    document.getElementById('prodPrice').value = p.price;
    document.getElementById('prodStock').value = p.stock;
    document.getElementById('prodUnit').value = p.unit;
    document.getElementById('prodThreshold').value = p.low_stock_threshold;
    document.getElementById('prodImageUrl').value = p.image_url || '';
    document.getElementById('productModalTitle').innerText = 'Edit Product';
    openModal('productModal');
}

async function saveProduct(e) {
    e.preventDefault();
    const id = document.getElementById('prodId').value;
    const fileInput = document.getElementById('prodImage');
    let imgUrl = document.getElementById('prodImageUrl').value;

    if (fileInput.files.length > 0) {
        const formData = new FormData();
        formData.append('image', fileInput.files[0]);
        const uploadRes = await fetch('/api/inventory/upload_image', { method: 'POST', body: formData });
        const uploadData = await uploadRes.json();
        if (uploadRes.ok) imgUrl = uploadData.image_url;
    }

    const payload = {
        name: document.getElementById('prodName').value,
        category: document.getElementById('prodCategory').value,
        price: parseFloat(document.getElementById('prodPrice').value),
        stock: parseInt(document.getElementById('prodStock').value),
        unit: document.getElementById('prodUnit').value,
        low_stock_threshold: parseInt(document.getElementById('prodThreshold').value),
        image_url: imgUrl
    };

    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/inventory/products/${id}` : `/api/inventory/products`;

    const res = await api(url, method, payload);
    if (res) {
        showToast(`Product ${id ? 'updated' : 'added'}!`);
        closeModal('productModal');
        loadProducts();
    }
}

async function deleteProduct(id) {
    if (!confirm('Delete this product?')) return;
    const res = await api(`/api/inventory/products/${id}`, 'DELETE');
    if (res) {
        showToast('Product deleted');
        loadProducts();
    }
}

// Billing Logic
async function loadCustomerDropdown() {
    const data = await api('/api/billing/customers');
    if (data) {
        allCustomers = data.customers;
        const sel = document.getElementById('billCustomerSelect');
        sel.innerHTML = allCustomers.map(c => `<option value="${c.id}">${c.name} (${c.phone})</option>`).join('');
    }
}

function openStartBillModal() {
    loadCustomerDropdown();
    document.getElementById('billCustomerName').value = '';
    toggleBillTypeFields();
    openModal('startBillModal');
}

function toggleBillTypeFields() {
    const type = document.getElementById('billTypeSelect').value;
    document.getElementById('instantNameGroup').style.display = type === 'instant' ? 'block' : 'none';
    document.getElementById('creditCustomerGroup').style.display = type === 'credit' ? 'block' : 'none';
}

function initBillSession() {
    const type = document.getElementById('billTypeSelect').value;
    const name = document.getElementById('billCustomerName').value;
    const custId = document.getElementById('billCustomerSelect').value;

    if (type === 'instant' && !name) return showToast('Please enter customer name', 'error');
    if (type === 'credit' && !custId) return showToast('Please select a customer', 'error');

    cartSession = {
        type: type,
        customerId: type === 'credit' ? custId : null,
        customerName: type === 'instant' ? name : null,
        items: []
    };

    closeModal('startBillModal');
    document.getElementById('cartOverlay').classList.add('active');
    document.querySelector('.main-content').classList.add('cart-active');

    switchTab('inventory');
    renderProducts();
    updateCartUI();
}

function cancelBill() {
    cartSession = null;
    document.getElementById('cartOverlay').classList.remove('active');
    document.querySelector('.main-content').classList.remove('cart-active');
    renderProducts();
}

function addToCart(productId) {
    const p = allProducts.find(x => x.id === productId);
    if (p.stock <= 0) return showToast('Out of stock!', 'error');

    const existing = cartSession.items.find(i => i.product.id === productId);
    if (existing) {
        if (existing.qty >= p.stock) return showToast('Max stock reached', 'error');
        existing.qty++;
    } else {
        cartSession.items.push({ product: p, qty: 1 });
    }
    updateCartUI();
}

function changeCartQty(index, delta) {
    const item = cartSession.items[index];
    item.qty += delta;
    if (item.qty <= 0) {
        cartSession.items.splice(index, 1);
    } else if (item.qty > item.product.stock) {
        item.qty = item.product.stock;
        showToast('Max stock reached', 'warning');
    }
    updateCartUI();
}

function updateCartUI() {
    if (!cartSession) return;
    document.getElementById('cartTypeBadge').innerText = cartSession.type.toUpperCase();
    document.getElementById('cartCustomerInfo').innerText = cartSession.type === 'instant' ? `Customer: ${cartSession.customerName}` : 'Credit Account Billing';

    const list = document.getElementById('cartItemsList');
    list.innerHTML = '';
    let total = 0;

    cartSession.items.forEach((item, idx) => {
        const sub = item.qty * item.product.price;
        total += sub;
        list.innerHTML += `
            <div class="cart-item">
                <div style="flex:1;">
                    <div style="font-weight:600;">${item.product.name}</div>
                    <div class="text-dim">₹${item.product.price} x ${item.qty} ${item.product.unit}</div>
                </div>
                <div class="qty-controls">
                    <button class="qty-btn" onclick="changeCartQty(${idx}, -1)">-</button>
                    <span>${item.qty}</span>
                    <button class="qty-btn" onclick="changeCartQty(${idx}, 1)">+</button>
                </div>
            </div>
        `;
    });
    document.getElementById('cartTotal').innerText = `₹${total.toFixed(2)}`;
}

function proceedToCheckout() {
    if (cartSession.items.length === 0) return showToast('Cart is empty', 'error');
    const total = cartSession.items.reduce((s, i) => s + (i.qty * i.product.price), 0);
    document.getElementById('checkoutDetails').innerHTML = `
        <p><strong>Type:</strong> ${cartSession.type.toUpperCase()}</p>
        <p><strong>Total Amount:</strong> ₹${total.toFixed(2)}</p>
    `;
    const paymentGroup = document.getElementById('paymentModeGroup');
    const qrContainer = document.getElementById('qrCodeContainer');
    const confirmBtn = document.querySelector('#checkoutModal .btn-success');

    if (cartSession.type === 'credit') {
        paymentGroup.style.display = 'none';
        qrContainer.style.display = 'none';
        confirmBtn.innerText = 'Confirm Credit Bill';
    } else {
        paymentGroup.style.display = 'block';
        document.getElementById('paymentModeSelect').value = 'cash';
        qrContainer.style.display = 'none';
        confirmBtn.innerText = 'Mark as Paid & Generate Bill';
    }
    openModal('checkoutModal');
}

function generateQR() {
    const mode = document.getElementById('paymentModeSelect').value;
    const qrContainer = document.getElementById('qrCodeContainer');
    if (mode === 'upi') {
        const total = cartSession.items.reduce((s, i) => s + (i.qty * i.product.price), 0);
        const upiUrl = `upi://pay?pa=shop@upi&pn=SmartRetail&am=${total.toFixed(2)}&cu=INR`;
        document.getElementById('qrImage').src = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(upiUrl)}`;
        qrContainer.style.display = 'flex';
    } else {
        qrContainer.style.display = 'none';
    }
}

async function confirmBill() {
    const payload = {
        bill_type: cartSession.type,
        customer_id: cartSession.customerId,
        customer_name: cartSession.customerName,
        payment_mode: cartSession.type === 'instant' ? document.getElementById('paymentModeSelect').value : null,
        items: cartSession.items.map(i => ({ product_id: i.product.id, quantity: i.qty }))
    };
    const res = await api('/api/billing/create', 'POST', payload);
    if (res) {
        showToast('Bill created successfully!');
        closeModal('checkoutModal');
        cancelBill();
        loadDashboardStats();
        switchTab('bills');
    }
}

// Bills & Payments
async function loadBills() {
    const data = await api('/api/billing/all');
    if (!data) return;
    const tbody = document.getElementById('billsTableBody');
    tbody.innerHTML = data.bills.map(b => `
        <tr>
            <td>#${b.id}</td>
            <td>${new Date(b.created_at).toLocaleDateString()}</td>
            <td><span class="badge ${b.bill_type === 'credit' ? 'badge-warning' : 'badge-success'}">${b.bill_type.toUpperCase()}</span></td>
            <td>${b.customer_name || 'Reg. Customer ' + (b.customer_id || '')}</td>
            <td>₹${b.final_amount.toFixed(2)}</td>
            <td><span class="badge ${b.status === 'paid' ? 'badge-success' : 'badge-danger'}">${b.status.toUpperCase()}</span></td>
            <td><button class="btn btn-sm btn-primary" onclick="viewBill(${b.id})">View</button></td>
        </tr>
    `).join('');
}

async function viewBill(id) {
    const data = await api(`/api/billing/${id}`);
    if (!data || !data.bill) return;
    const b = data.bill;
    document.getElementById('receiptTitle').innerText = `Receipt #${b.id}`;
    document.getElementById('receiptDetails').innerHTML = `
        <strong>Date:</strong> ${new Date(b.created_at).toLocaleString()}<br>
        <strong>Customer:</strong> ${b.customer_name || (b.customer_id ? 'ID: ' + b.customer_id : 'Instant Walk-in')}<br>
        <strong>Type:</strong> <span class="badge ${b.bill_type === 'credit' ? 'badge-warning' : 'badge-success'}">${b.bill_type.toUpperCase()}</span> 
        <strong>Status:</strong> <span class="badge ${b.status === 'paid' ? 'badge-success' : 'badge-danger'}">${b.status.toUpperCase()}</span>
    `;
    const tbody = document.getElementById('receiptItems');
    tbody.innerHTML = b.items.map(i => `
        <tr style="border-bottom: 1px solid var(--border);">
            <td style="padding: 0.6rem 0;">ID: ${i.product_id}</td>
            <td style="padding: 0.6rem 0;">${i.quantity}</td>
            <td style="padding: 0.6rem 0;">₹${i.price_per_unit.toFixed(2)}</td>
            <td style="padding: 0.6rem 0; font-weight: 600;">₹${i.subtotal.toFixed(2)}</td>
        </tr>`).join('');
    document.getElementById('receiptTotal').innerText = `₹${b.final_amount.toFixed(2)}`;
    openModal('receiptModal');
}

async function loadPayments() {
    const data = await api('/api/payments/all');
    if (!data) return;
    const tbody = document.getElementById('paymentsTableBody');
    tbody.innerHTML = data.payments.map(p => `
        <tr>
            <td>#${p.id}</td>
            <td>${new Date(p.created_at).toLocaleDateString()}</td>
            <td>${p.customer_id ? ('Customer ID: ' + p.customer_id) : 'Instant Walk-in'}</td>
            <td class="text-success font-weight-bold">₹${p.amount.toFixed(2)}</td>
            <td>${p.payment_mode.toUpperCase()}</td>
            <td>${p.note || '-'}</td>
        </tr>
    `).join('');
}

async function openRecordPaymentModal() {
    if (allCustomers.length === 0) {
        const data = await api('/api/billing/customers');
        if (data) allCustomers = data.customers;
    }
    const sel = document.getElementById('payCustomerSelect');
    sel.innerHTML = allCustomers.map(c => `<option value="${c.id}">${c.name} (${c.phone})</option>`).join('');
    document.getElementById('payAmount').value = '';
    document.getElementById('payNote').value = '';
    openModal('recordPaymentModal');
}

async function updateDueInModal() {
    const id = document.getElementById('payCustomerSelect').value;
    if (!id) return;
    const data = await api(`/api/customer/due/${id}`);
    if (data) {
        if (data.is_advance) {
            document.getElementById('payAmount').value = 0;
            document.getElementById('modalDueInfo').innerHTML = `<span class="text-success" style="font-weight:600;">Customer has Advance Balance: ₹${data.absolute_balance.toFixed(2)}</span>`;
        } else {
            document.getElementById('payAmount').value = data.absolute_balance;
            document.getElementById('modalDueInfo').innerText = `Current Pending Due: ₹${data.absolute_balance.toFixed(2)}`;
        }
    }
}

async function submitRecordPayment() {
    const submitBtn = document.getElementById('submitPaymentBtn');
    const payload = {
        customer_id: document.getElementById('payCustomerSelect').value,
        amount: parseFloat(document.getElementById('payAmount').value),
        payment_mode: document.getElementById('payMode').value,
        note: document.getElementById('payNote').value
    };
    if (!payload.amount || payload.amount <= 0) return showToast('Enter valid amount', 'error');
    submitBtn.disabled = true;
    submitBtn.innerText = 'Processing...';
    const res = await api('/api/payments/record', 'POST', payload);
    if (res) {
        showToast('Payment recorded!');
        closeModal('recordPaymentModal');
        loadPayments();
        loadBills();
        loadDashboardStats();
    }
    submitBtn.disabled = false;
    submitBtn.innerText = 'Save Payment';
}

// Customers
async function loadCustomersView() {
    const data = await api('/api/billing/customers');
    if (!data) return;
    allCustomers = data.customers;
    const list = document.getElementById('customersList');
    list.innerHTML = allCustomers.map(c => `
        <div class="customer-list-item" onclick="viewCustomer(${c.id})" style="${c.status === 'pending' ? 'border-left: 4px solid var(--warning); background: rgba(245, 158, 11, 0.05);' : ''}">
            <div>
                <div style="font-weight: 600; font-size: 1.1rem; display: flex; align-items: center; gap: 0.5rem;">
                    ${c.name}
                    ${c.status === 'pending' ? '<span class="badge badge-warning" style="font-size: 0.6rem;">PENDING</span>' : ''}
                </div>
                <div class="text-dim">${c.phone}</div>
            </div>
            <div class="text-primary" style="font-weight: 600;">View Analytics →</div>
        </div>
    `).join('');
}

async function viewCustomer(id) {
    document.getElementById('customerModalTitle').innerText = 'Loading...';
    openModal('customerModal');
    const billsData = await api(`/api/billing/customer/${id}`);
    const user = allCustomers.find(u => u.id === id);
    document.getElementById('customerModalTitle').innerText = user.name;
    const approvalSection = document.getElementById('approvalSection');
    if (user.status === 'pending') {
        approvalSection.style.display = 'block';
        approvalSection.dataset.userId = id;
    } else {
        approvalSection.style.display = 'none';
    }
    const dueData = await api(`/api/customer/due/${id}`);
    if (dueData) {
        document.getElementById('custTotalSpent').innerText = `₹${dueData.total_credit_bills.toFixed(2)}`;
        if (dueData.is_advance) {
            document.getElementById('custDue').innerText = `Advance: ₹${dueData.absolute_balance.toFixed(2)}`;
            document.getElementById('custDue').className = 'stat-value text-success';
        } else {
            document.getElementById('custDue').innerText = `Due: ₹${dueData.absolute_balance.toFixed(2)}`;
            document.getElementById('custDue').className = 'stat-value text-warning';
        }
    }
    if (billsData) {
        document.getElementById('customerBillsBody').innerHTML = billsData.bills.map(b => `
            <tr>
                <td>${new Date(b.created_at).toLocaleDateString()}</td>
                <td>₹${b.final_amount.toFixed(2)}</td>
                <td><span class="badge ${b.status === 'paid' ? 'badge-success' : 'badge-danger'}">${b.status.toUpperCase()}</span></td>
            </tr>`).join('');
    }
    const paymentsData = await api(`/api/payments/customer/${id}`);
    if (paymentsData && paymentsData.payments) {
        document.getElementById('customerPaymentsBody').innerHTML = paymentsData.payments.map(p => `
            <tr>
                <td>${new Date(p.created_at).toLocaleDateString()}</td>
                <td class="text-success">₹${p.amount.toFixed(2)}</td>
                <td>${p.payment_mode.toUpperCase()}</td>
            </tr>`).join('');
    } else {
        document.getElementById('customerPaymentsBody').innerHTML = '<tr><td colspan="3" class="text-center">No payments found</td></tr>';
    }
}

async function approveCustomer() {
    const id = document.getElementById('approvalSection').dataset.userId;
    const res = await api(`/api/auth/approve/${id}`, 'POST');
    if (res) {
        showToast('Customer approved!');
        closeModal('customerModal');
        loadCustomersView();
    }
}

// Shop Status Management
async function loadShopStatus() {
    const data = await api('/api/agent/shop-status');
    if (data) {
        const toggle = document.getElementById('shopStatusToggle');
        const label = document.getElementById('shopStatusLabel');
        if (toggle && label) {
            toggle.checked = data.status === 'open';
            label.innerText = `Shop: ${data.status === 'open' ? 'Open' : 'Closed'}`;
            label.style.color = data.status === 'open' ? 'var(--success)' : 'var(--danger)';
        }
    }
}

async function toggleShopStatus() {
    const res = await api('/api/agent/toggle-shop', 'POST');
    if (res) {
        showToast(`Shop is now ${res.status.toUpperCase()}`);
        loadShopStatus();
    }
}
