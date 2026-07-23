/* ============================================================
   app.js  —  종량제 봉투 판매 관리 모바일 웹 SPA 프론트엔드 로직
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  initClock();
  initNavigation();
  loadMasterData();
  loadDashboard();
  setDefaultDates();
});

// ── 실시간 시계 ──────────────────────────────────────────────
function initClock() {
  const clockEl = document.getElementById('header-clock');
  if (!clockEl) return;
  const update = () => {
    const now = new Date();
    const str = now.toLocaleDateString('kr-KR', { month: '2-digit', day: '2-digit' }) + ' ' +
                now.toLocaleTimeString('kr-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
    clockEl.textContent = str;
  };
  update();
  setInterval(update, 1000);
}

function setDefaultDates() {
  const today = new Date().toISOString().split('T')[0];
  const saleDateInput = document.getElementById('sale-date');
  const collectionDateInput = document.getElementById('collection-date');
  const inboundDateInput = document.getElementById('inbound-date');
  
  if (saleDateInput) saleDateInput.value = today;
  if (collectionDateInput) collectionDateInput.value = today;
  if (inboundDateInput) inboundDateInput.value = today;
}

// ── 모바일 네비게이션 탭 전환 ─────────────────────────────
function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const targetTab = item.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));

  const activeBtn = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
  const activeTab = document.getElementById(`tab-${tabId}`);

  if (activeBtn) activeBtn.classList.add('active');
  if (activeTab) activeTab.classList.add('active');

  // 탭 변경 시 데이터 새로고침
  if (tabId === 'dashboard') loadDashboard();
  if (tabId === 'sales') loadSalesList();
  if (tabId === 'ar') loadARList();
  if (tabId === 'stock') loadStockList();
  if (tabId === 'customer') loadCustomerList();
}

// ── 포맷팅 헬퍼 ──────────────────────────────────────────────
function fmtCurrency(val) {
  return (val || 0).toLocaleString() + '원';
}

function fmtQty(val) {
  return (val || 0).toLocaleString() + '개';
}

// ── 마스터 데이터 (품목 & 거래처 콤보) 로드 ──────────────────
let globalProducts = [];
let globalCustomers = [];

async function loadMasterData() {
  try {
    const [pRes, cRes] = await Promise.all([
      fetch('/api/products').then(r => r.json()),
      fetch('/api/customers').then(r => r.json())
    ]);

    if (pRes.status === 'success') {
      globalProducts = pRes.specs;
      populateSpecCombos(pRes.specs);
    }
    if (cRes.status === 'success') {
      globalCustomers = cRes.customers;
      populateCustomerCombos(cRes.customers);
    }
  } catch (err) {
    console.error("마스터 데이터 로드 실패:", err);
  }
}

function populateSpecCombos(specs) {
  const saleSpecSelect = document.getElementById('sale-spec');
  const inboundSpecSelect = document.getElementById('inbound-spec');

  const optionsHtml = '<option value="">선택하세요</option>' +
    specs.map(s => `<option value="${s.id}" data-price="${s.unit_price}">[${s.type_name}] ${s.name} (${fmtCurrency(s.unit_price)})</option>`).join('');

  if (saleSpecSelect) {
    saleSpecSelect.innerHTML = optionsHtml;
    saleSpecSelect.addEventListener('change', (e) => {
      const selected = e.target.options[e.target.selectedIndex];
      const price = selected.getAttribute('data-price');
      const unitPriceInput = document.getElementById('sale-unit-price');
      if (unitPriceInput && price) {
        unitPriceInput.value = price;
        calculateTotalAmount();
      }
    });
  }

  if (inboundSpecSelect) {
    inboundSpecSelect.innerHTML = optionsHtml;
  }
}

function populateCustomerCombos(customers) {
  const saleCustSelect = document.getElementById('sale-customer');
  const collectionCustSelect = document.getElementById('collection-customer');

  const optionsHtml = '<option value="">선택하세요</option>' +
    customers.filter(c => c.is_active).map(c => `<option value="${c.id}">[${c.district || '공통'}] ${c.name}</option>`).join('');

  if (saleCustSelect) saleCustSelect.innerHTML = optionsHtml;
  if (collectionCustSelect) collectionCustSelect.innerHTML = optionsHtml;
}

// ── 1. 대시보드 로드 ─────────────────────────────────────────
async function loadDashboard() {
  try {
    const res = await fetch('/api/dashboard').then(r => r.json());
    if (res.status === 'success') {
      document.getElementById('dash-today-sales').textContent = fmtCurrency(res.today_total_amount);
      document.getElementById('dash-today-qty').textContent = fmtQty(res.today_total_quantity);
      document.getElementById('dash-total-ar').textContent = fmtCurrency(res.total_ar_balance);
      document.getElementById('dash-month-sales').textContent = fmtCurrency(res.month_total_amount);
    }
  } catch (err) {
    console.error("대시보드 로드 실패:", err);
  }
}

// ── 2. 판매 입력 & 내역 ──────────────────────────────────────
function calculateTotalAmount() {
  const qty = parseInt(document.getElementById('sale-qty').value || 0);
  const price = parseInt(document.getElementById('sale-unit-price').value || 0);
  const totalInput = document.getElementById('sale-total-amount');
  if (totalInput) {
    totalInput.value = (qty * price).toLocaleString() + ' 원';
  }
}

document.getElementById('sale-qty')?.addEventListener('input', calculateTotalAmount);
document.getElementById('sale-unit-price')?.addEventListener('input', calculateTotalAmount);

async function submitSale() {
  const date = document.getElementById('sale-date').value;
  const customerId = parseInt(document.getElementById('sale-customer').value);
  const specId = parseInt(document.getElementById('sale-spec').value);
  const qty = parseInt(document.getElementById('sale-qty').value);
  const unitPrice = parseInt(document.getElementById('sale-unit-price').value);
  const payMethod = document.getElementById('sale-payment-method').value;
  const memo = document.getElementById('sale-memo').value;

  if (!date || !customerId || !specId || !qty) {
    alert("필수 항목(날짜, 거래처, 규격, 수량)을 올바르게 입력해주세요.");
    return;
  }

  try {
    const res = await fetch('/api/sales', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sale_date: date,
        customer_id: customerId,
        spec_id: specId,
        quantity: qty,
        unit_price: unitPrice,
        payment_method: payMethod,
        memo: memo
      })
    }).then(r => r.json());

    if (res.status === 'success') {
      alert("✅ 판매 내역이 등록되었습니다.");
      document.getElementById('sale-qty').value = '';
      document.getElementById('sale-memo').value = '';
      calculateTotalAmount();
      loadSalesList();
      loadDashboard();
    } else {
      alert("오류: " + res.detail);
    }
  } catch (err) {
    alert("서버 통신 실패: " + err);
  }
}

async function loadSalesList() {
  const listEl = document.getElementById('sales-list');
  if (!listEl) return;
  const today = new Date().toISOString().split('T')[0];
  try {
    const res = await fetch(`/api/sales?date=${today}`).then(r => r.json());
    if (res.status === 'success') {
      if (res.sales.length === 0) {
        listEl.innerHTML = '<div class="list-item"><div class="list-item-sub">오늘 등록된 판매 내역이 없습니다.</div></div>';
        return;
      }
      listEl.innerHTML = res.sales.map(s => `
        <div class="list-item">
          <div>
            <div class="list-item-title">${s.customer_name} <span class="badge badge-blue">${s.payment_method}</span></div>
            <div class="list-item-sub">[${s.type_name}] ${s.spec_name} · ${fmtQty(s.quantity)}</div>
          </div>
          <div>
            <div class="list-item-val">${fmtCurrency(s.total_amount)}</div>
            <button class="btn btn-danger btn-sm" onclick="deleteSale(${s.id})" style="margin-top:4px;">삭제</button>
          </div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error("판매 내역 로드 실패:", err);
  }
}

async function deleteSale(saleId) {
  if (!confirm("이 판매 내역을 삭제하시겠습니까? (재고/미수금이 자동 원복됩니다)")) return;
  try {
    const res = await fetch(`/api/sales/${saleId}`, { method: 'DELETE' }).then(r => r.json());
    if (res.status === 'success') {
      loadSalesList();
      loadDashboard();
    }
  } catch (err) {
    alert("삭제 실패: " + err);
  }
}

// ── 3. 미수 관리 (AR) ───────────────────────────────────────
async function loadARList() {
  const listEl = document.getElementById('ar-list');
  if (!listEl) return;
  try {
    const res = await fetch('/api/ar').then(r => r.json());
    if (res.status === 'success') {
      listEl.innerHTML = res.ar_balances.map(ar => `
        <div class="list-item">
          <div>
            <div class="list-item-title">[${ar.district || '공통'}] ${ar.name}</div>
            <div class="list-item-sub">전화: ${ar.phone || '-'}</div>
          </div>
          <div>
            <div class="list-item-val ${ar.ar_balance > 0 ? 'red' : ''}">${fmtCurrency(ar.ar_balance)}</div>
            <button class="btn btn-success btn-sm" onclick="openCollectionModal(${ar.id}, '${ar.name}')" style="margin-top:4px;">수금 입력</button>
          </div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error("미수 목록 로드 실패:", err);
  }
}

function openCollectionModal(custId, custName) {
  const modal = document.getElementById('collection-modal');
  const select = document.getElementById('collection-customer');
  if (select) select.value = custId;
  if (modal) modal.classList.add('active');
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('active');
}

async function submitCollection() {
  const date = document.getElementById('collection-date').value;
  const custId = parseInt(document.getElementById('collection-customer').value);
  const amount = parseInt(document.getElementById('collection-amount').value);
  const payMethod = document.getElementById('collection-payment-method').value;
  const memo = document.getElementById('collection-memo').value;

  if (!date || !custId || !amount) {
    alert("수금 날짜, 거래처, 수금 금액을 입력해주세요.");
    return;
  }

  try {
    const res = await fetch('/api/ar/collection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        collection_date: date,
        customer_id: custId,
        amount: amount,
        payment_method: payMethod,
        memo: memo
      })
    }).then(r => r.json());

    if (res.status === 'success') {
      alert("✅ 수금 처리되었습니다.");
      closeModal('collection-modal');
      document.getElementById('collection-amount').value = '';
      loadARList();
      loadDashboard();
    }
  } catch (err) {
    alert("수금 실패: " + err);
  }
}

// ── 4. 재고 관리 ─────────────────────────────────────────────
async function loadStockList() {
  const listEl = document.getElementById('stock-list');
  if (!listEl) return;
  try {
    const res = await fetch('/api/stock').then(r => r.json());
    if (res.status === 'success') {
      listEl.innerHTML = res.stock.map(st => `
        <div class="list-item">
          <div>
            <div class="list-item-title">[${st.type_name}] ${st.spec_name}</div>
            <div class="list-item-sub">코드: ${st.product_code || '-'} · 단가: ${fmtCurrency(st.unit_price)}</div>
          </div>
          <div>
            <div class="list-item-val ${st.current_stock < 100 ? 'red' : 'green'}">${fmtQty(st.current_stock)}</div>
          </div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error("재고 목록 로드 실패:", err);
  }
}

// ── 5. 거래처 관리 ───────────────────────────────────────────
async function loadCustomerList() {
  const listEl = document.getElementById('customer-list');
  if (!listEl) return;
  try {
    const res = await fetch('/api/customers').then(r => r.json());
    if (res.status === 'success') {
      listEl.innerHTML = res.customers.map(c => `
        <div class="list-item">
          <div>
            <div class="list-item-title">${c.name} <span class="badge ${c.customer_type==='입고처' ? 'badge-blue':'badge-orange'}">${c.customer_type}</span></div>
            <div class="list-item-sub">지역: ${c.district || '공통'} · 전화: ${c.phone || '-'}</div>
          </div>
          <div>
            <button class="btn btn-danger btn-sm" onclick="deleteCustomer(${c.id}, '${c.name}')">삭제</button>
          </div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error("거래처 목록 로드 실패:", err);
  }
}

async function submitCustomer() {
  const name = document.getElementById('cust-name').value;
  const ctype = document.getElementById('cust-type').value;
  const district = document.getElementById('cust-district').value;
  const phone = document.getElementById('cust-phone').value;

  if (!name) {
    alert("거래처명을 입력해주세요.");
    return;
  }

  try {
    const res = await fetch('/api/customers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name,
        customer_type: ctype,
        district: district,
        phone: phone
      })
    }).then(r => r.json());

    if (res.status === 'success') {
      alert("✅ 거래처가 등록되었습니다.");
      closeModal('customer-modal');
      document.getElementById('cust-name').value = '';
      loadCustomerList();
      loadMasterData();
    }
  } catch (err) {
    alert("등록 실패: " + err);
  }
}

async function deleteCustomer(cid, name) {
  if (!confirm(`'${name}' 거래처를 삭제하시겠습니까?`)) return;
  try {
    const res = await fetch(`/api/customers/${cid}`, { method: 'DELETE' }).then(r => r.json());
    if (res.status === 'warning') {
      if (confirm(res.message)) {
        await fetch(`/api/customers/${cid}/deactivate`, { method: 'POST' });
        loadCustomerList();
        loadMasterData();
      }
    } else if (res.status === 'success') {
      alert("✅ 거래처가 완전 삭제되었습니다.");
      loadCustomerList();
      loadMasterData();
    }
  } catch (err) {
    alert("삭제 실패: " + err);
  }
}
