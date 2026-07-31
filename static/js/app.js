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
  const searchStartInput = document.getElementById('search-start-date');
  const searchEndInput = document.getElementById('search-end-date');
  
  if (saleDateInput) saleDateInput.value = today;
  if (collectionDateInput) collectionDateInput.value = today;
  if (inboundDateInput) inboundDateInput.value = today;
  if (searchStartInput) searchStartInput.value = today;
  if (searchEndInput) searchEndInput.value = today;
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
    specs.map(s => `<option value="${s.id}" data-price="${s.unit_price}">[${s.type_name}] ${s.spec_name} (${fmtCurrency(s.unit_price)})</option>`).join('');

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
  const districtFilter = document.getElementById('sale-district-filter');

  // 동 목록 추출 (중복 제거, 빈값 제외)
  if (districtFilter) {
    const districts = [...new Set(
      customers.filter(c => c.is_active && c.district).map(c => c.district.trim())
    )].sort();
    districtFilter.innerHTML = '<option value="">전체 거래처</option>' +
      districts.map(d => `<option value="${d}">${d}</option>`).join('');
  }

  // 전체 거래처 옵션 저장
  window._allCustomers = customers;

  const activeCustomers = customers.filter(c => c.is_active);
  const optionsHtml = '<option value="">선택하세요</option>' +
    activeCustomers.map(c => `<option value="${c.id}" data-district="${c.district || ''}">[${c.district || '공통'}] ${c.name}</option>`).join('');

  if (saleCustSelect) saleCustSelect.innerHTML = optionsHtml;
  if (collectionCustSelect) collectionCustSelect.innerHTML = optionsHtml;

  // 검색 거래처 드롭다운 (전체 거래처 옵션 포함)
  const searchCustSelect = document.getElementById('search-customer');
  if (searchCustSelect) {
    searchCustSelect.innerHTML = '<option value="">전체 거래처</option>' +
      activeCustomers.map(c => `<option value="${c.id}">[${c.district || '공통'}] ${c.name}</option>`).join('');
  }
}

// 동 필터 변경 시 거래처 목록 갱신
function onDistrictFilterChange() {
  const selectedDistrict = document.getElementById('sale-district-filter').value;
  const saleCustSelect = document.getElementById('sale-customer');
  if (!saleCustSelect || !window._allCustomers) return;

  const filtered = window._allCustomers.filter(c => {
    if (!c.is_active) return false;
    if (!selectedDistrict) return true;
    return (c.district || '').trim() === selectedDistrict;
  });

  saleCustSelect.innerHTML = '<option value="">선택하세요</option>' +
    filtered.map(c => `<option value="${c.id}">[${c.district || '공통'}] ${c.name}</option>`).join('');
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

// 결제 방법 변경 시 복합결제 입력 UI 표시/숨김
function onPaymentMethodChange() {
  const method = document.getElementById('sale-payment-method').value;
  const mixedArea = document.getElementById('mixed-payment-area');
  if (!mixedArea) return;
  if (method === '현금+카드') {
    mixedArea.style.display = 'block';
    updateMixedPaymentBalance();
  } else {
    mixedArea.style.display = 'none';
  }
}

function updateMixedPaymentBalance() {
  const qty = parseInt(document.getElementById('sale-qty').value || 0);
  const price = parseInt(document.getElementById('sale-unit-price').value || 0);
  const total = qty * price;
  const cash = parseInt(document.getElementById('sale-cash-amount').value || 0);
  const card = parseInt(document.getElementById('sale-card-amount').value || 0);
  const balanceEl = document.getElementById('mixed-balance');
  if (balanceEl) {
    const diff = total - cash - card;
    balanceEl.textContent = `합계: ${total.toLocaleString()}원 / 현금+카드: ${(cash+card).toLocaleString()}원 / 차액: ${diff.toLocaleString()}원`;
    balanceEl.style.color = diff === 0 ? '#27ae60' : '#e74c3c';
  }
}

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

  let cashAmount = 0, cardAmount = 0;
  if (payMethod === '현금+카드') {
    cashAmount = parseInt(document.getElementById('sale-cash-amount').value || 0);
    cardAmount = parseInt(document.getElementById('sale-card-amount').value || 0);
    const total = qty * unitPrice;
    if (cashAmount + cardAmount !== total) {
      alert(`현금(${cashAmount.toLocaleString()}원) + 카드(${cardAmount.toLocaleString()}원) = ${(cashAmount+cardAmount).toLocaleString()}원\n총 결제금액(${total.toLocaleString()}원)과 일치해야 합니다.`);
      return;
    }
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
        cash_amount: cashAmount,
        card_amount: cardAmount,
        memo: memo
      })
    }).then(r => r.json());

    if (res.status === 'success') {
      alert("✅ 판매 내역이 등록되었습니다.");
      document.getElementById('sale-qty').value = '';
      document.getElementById('sale-memo').value = '';
      const mixedArea = document.getElementById('mixed-payment-area');
      if (mixedArea) {
        document.getElementById('sale-cash-amount').value = '';
        document.getElementById('sale-card-amount').value = '';
        mixedArea.style.display = 'none';
      }
      document.getElementById('sale-payment-method').value = '현금';
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
  // 요약 숨기기
  const summaryEl = document.getElementById('search-summary');
  if (summaryEl) summaryEl.style.display = 'none';
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

async function searchSalesHistory() {
  const startDate = document.getElementById('search-start-date').value;
  const endDate = document.getElementById('search-end-date').value;
  const customerId = document.getElementById('search-customer').value;
  const listEl = document.getElementById('sales-list');
  if (!listEl) return;

  if (!startDate || !endDate) {
    alert('시작일과 종료일을 입력해주세요.');
    return;
  }

  let url = `/api/sales?start_date=${startDate}&end_date=${endDate}`;
  if (customerId) url += `&customer_id=${customerId}`;

  listEl.innerHTML = '<div class="list-item"><div class="list-item-sub">조회 중...</div></div>';

  try {
    const res = await fetch(url).then(r => r.json());
    if (res.status === 'success') {
      // 요약 표시
      const summaryEl = document.getElementById('search-summary');
      if (summaryEl) {
        const totalQty = res.sales.reduce((s, r) => s + (r.quantity || 0), 0);
        const totalAmt = res.sales.reduce((s, r) => s + (r.total_amount || 0), 0);
        document.getElementById('search-count').textContent = res.sales.length;
        document.getElementById('search-qty').textContent = totalQty.toLocaleString();
        document.getElementById('search-total').textContent = fmtCurrency(totalAmt);
        summaryEl.style.display = 'block';
      }

      if (res.sales.length === 0) {
        listEl.innerHTML = '<div class="list-item"><div class="list-item-sub">해당 기간에 판매 내역이 없습니다.</div></div>';
        return;
      }
      listEl.innerHTML = res.sales.map(s => `
        <div class="list-item">
          <div>
            <div class="list-item-title">${s.customer_name} <span class="badge badge-blue">${s.payment_method}</span></div>
            <div class="list-item-sub">${s.sale_date} · [${s.type_name}] ${s.spec_name} · ${fmtQty(s.quantity)}</div>
          </div>
          <div>
            <div class="list-item-val">${fmtCurrency(s.total_amount)}</div>
          </div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error('판매 이력 조회 실패:', err);
    listEl.innerHTML = '<div class="list-item"><div class="list-item-sub" style="color:#ef4444;">조회 실패: ' + err + '</div></div>';
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
function exportARExcel() {
  window.location.href = '/api/ar/export';
}

let globalARBalances = [];

async function loadARList() {
  const listEl = document.getElementById('ar-list');
  if (!listEl) return;
  try {
    const res = await fetch('/api/ar').then(r => r.json());
    if (res.status === 'success') {
      globalARBalances = res.ar_balances;
      const totalAR = res.ar_balances.reduce((s, ar) => s + ar.ar_balance, 0);
      listEl.innerHTML = `
        <div class="list-item" style="background:rgba(231,76,60,0.08); border-radius:10px; margin-bottom:8px;">
          <div><div class="list-item-title">📋 미수금 총합</div></div>
          <div>
            <div class="list-item-val red" style="font-size:1.1rem;"><b>${fmtCurrency(totalAR)}</b></div>
            <button class="btn btn-success btn-sm" onclick="exportARExcel()" style="margin-top:4px;">📥 엑셀 다운로드</button>
          </div>
        </div>
      ` + res.ar_balances.map(ar => `
        <div class="list-item">
          <div>
            <div class="list-item-title">[${ar.district || '공통'}] ${ar.name}</div>
          </div>
          <div>
            <div class="list-item-val ${ar.ar_balance > 0 ? 'red' : ''}"><b>${fmtCurrency(ar.ar_balance)}</b></div>
            <button class="btn btn-success btn-sm" onclick="openCollectionModal(${ar.id}, '${ar.name}')" style="margin-top:4px;">수금</button>
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
  if (select) {
    select.value = custId;
    onCollectionCustomerChange(); // 잔액 업데이트
  }
  if (modal) modal.classList.add('active');
}

function onCollectionCustomerChange() {
  const select = document.getElementById('collection-customer');
  const balanceEl = document.getElementById('collection-current-balance');
  const amountInput = document.getElementById('collection-amount');
  
  if (!select || !balanceEl || !amountInput) return;
  
  const custId = parseInt(select.value);
  const arData = globalARBalances.find(ar => ar.id === custId);
  const balance = arData ? arData.ar_balance : 0;
  
  balanceEl.textContent = fmtCurrency(balance);
  balanceEl.style.color = balance > 0 ? '#ef4444' : '#10b981';
  balanceEl.dataset.balance = balance;
  
  // 수금액을 미수 잔액으로 자동 설정
  amountInput.value = Math.max(balance, 1);
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

  const balanceEl = document.getElementById('collection-current-balance');
  const currentBalance = balanceEl ? parseInt(balanceEl.dataset.balance || 0) : 0;
  
  if (amount > currentBalance) {
    if (!confirm(`현재 미수 잔액은 ${fmtCurrency(currentBalance)}입니다.\n입력하신 수금액 ${fmtCurrency(amount)}이(가) 잔액을 초과합니다.\n\n그래도 저장하시겠습니까?`)) {
      return;
    }
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
