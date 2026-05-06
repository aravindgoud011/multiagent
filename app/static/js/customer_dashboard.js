/**
 * Smart Retail — Customer Dashboard Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    loadSpendingInsights();
    setupNotifications();
});

async function loadDashboardData() {
    const data = await api('/api/customer/dashboard');
    if (!data) return;

    // Greeting
    document.getElementById('customerName').textContent = data.customer.name;
    document.getElementById('userAvatar').textContent = data.customer.name[0].toUpperCase();

    // Stats
    document.getElementById('stat-bills').textContent = data.stats.total_bills_count;
    document.getElementById('stat-paid').textContent = `₹${data.stats.total_paid.toLocaleString()}`;
    document.getElementById('stat-due').textContent = `₹${data.stats.total_due.toLocaleString()}`;
    document.getElementById('stat-points').textContent = data.stats.loyalty_points;

    // Bills Table
    renderBillsTable(data.recent_bills);
    
    // Transactions
    renderPaymentsTable(data.recent_payments);
}

function renderBillsTable(bills) {
    const tbody = document.getElementById('billsTableBody');
    tbody.innerHTML = bills.length ? '' : '<tr><td colspan="6" style="text-align:center;">No bills found.</td></tr>';
    
    bills.forEach(bill => {
        const date = new Date(bill.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
        const statusBadge = bill.status === 'paid' ? '<span class="badge badge-success">Paid</span>' : 
                          (bill.status === 'unpaid' ? '<span class="badge badge-warning">Pending</span>' : '<span class="badge badge-danger">Overdue</span>');
        
        tbody.innerHTML += `
            <tr>
                <td>#${bill.id}</td>
                <td>${date}</td>
                <td>₹${bill.total_amount.toLocaleString()}</td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn btn-outline btn-sm" onclick="viewInvoice(${bill.id})">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            </tr>
        `;
    });
}

function renderPaymentsTable(payments) {
    const tbody = document.getElementById('paymentsTableBody');
    tbody.innerHTML = payments.length ? '' : '<tr><td colspan="4" style="text-align:center;">No recent payments.</td></tr>';
    
    payments.forEach(pay => {
        const date = new Date(pay.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
        tbody.innerHTML += `
            <tr>
                <td>${date}</td>
                <td>₹${pay.amount.toLocaleString()}</td>
                <td style="text-transform: capitalize;">${pay.payment_mode}</td>
                <td><span class="badge badge-success">Successful</span></td>
            </tr>
        `;
    });
}

async function loadSpendingInsights() {
    const data = await api('/api/customer/spending-insights');
    if (!data || !data.spending.length) return;

    const ctx = document.getElementById('spendingChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.spending.map(i => i.month),
            datasets: [{
                label: 'Monthly Spending (₹)',
                data: data.spending.map(i => i.amount),
                borderColor: '#4f46e5',
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 3,
                pointBackgroundColor: '#4f46e5'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { display: false } },
                x: { grid: { display: false } }
            }
        }
    });
}

// Support & Tickets
async function raiseTicket() {
    const title = prompt("Enter a short title for your issue:");
    if (!title) return;
    const description = prompt("Describe the issue in detail:");
    if (!description) return;

    const res = await api('/api/customer/tickets', 'POST', { title, description, category: 'General' });
    if (res) {
        showToast("Ticket raised successfully! Our team will contact you.", "success");
    }
}

// Invoice Logic (Mock for now as per rules "Don't break logic")
async function viewInvoice(billId) {
    const billData = await api(`/api/billing/receipt/${billId}`);
    if (!billData) return;

    const details = document.getElementById('invoiceDetails');
    details.innerHTML = `
        <div style="border-bottom: 1px solid #eee; padding-bottom: 1rem; margin-bottom: 1rem;">
            <p><strong>Bill ID:</strong> #${billData.bill.id}</p>
            <p><strong>Date:</strong> ${new Date(billData.bill.created_at).toLocaleString()}</p>
            <p><strong>Type:</strong> ${billData.bill.bill_type.toUpperCase()}</p>
        </div>
        <table style="width: 100%; border-collapse: collapse;">
            <thead style="background: #f8fafc;">
                <tr><th style="padding: 0.5rem; text-align: left;">Item</th><th style="padding: 0.5rem; text-align: right;">Qty</th><th style="padding: 0.5rem; text-align: right;">Price</th></tr>
            </thead>
            <tbody>
                ${billData.items.map(item => `
                    <tr>
                        <td style="padding: 0.5rem; border-bottom: 1px solid #f1f5f9;">${item.product_name}</td>
                        <td style="padding: 0.5rem; border-bottom: 1px solid #f1f5f9; text-align: right;">${item.quantity}</td>
                        <td style="padding: 0.5rem; border-bottom: 1px solid #f1f5f9; text-align: right;">₹${item.subtotal}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
        <div style="margin-top: 1rem; text-align: right; font-weight: 700; font-size: 1.2rem;">
            Total: ₹${billData.bill.final_amount}
        </div>
    `;

    document.getElementById('invoiceModal').style.display = 'flex';
}

function closeInvoice() {
    document.getElementById('invoiceModal').style.display = 'none';
}

// Notification Logic
async function setupNotifications() {
    const data = await api('/api/notifications/customer/unread-count');
    if (data) {
        const badge = document.getElementById('notifBadge');
        badge.textContent = data.unread_count;
        badge.style.display = data.unread_count > 0 ? 'flex' : 'none';
    }
}

async function toggleNotifications() {
    const data = await api('/api/notifications/customer/all');
    if (!data) return;

    const list = document.getElementById('notifList');
    list.innerHTML = data.notifications.length ? '' : '<p style="padding: 1rem; text-align: center; color: #64748b;">No notifications.</p>';
    
    data.notifications.forEach(n => {
        list.innerHTML += `
            <div style="padding: 1rem; border-bottom: 1px solid #f1f5f9; ${n.is_read ? '' : 'background: #f0f7ff;'}">
                <p style="font-weight: 600; font-size: 0.85rem;">${n.title}</p>
                <p style="font-size: 0.8rem; color: #64748b;">${n.message}</p>
            </div>
        `;
    });
    
    document.getElementById('notifDropdown').classList.toggle('active');
}

// Chatbot UI Toggle
function toggleChat() {
    alert("Smart Retail AI Assistant is initializing... (Rule-based logic ready)");
}
