/**
 * ========================================
 * ZERO-REFRESH POLICY - GLOBAL AJAX HANDLER
 * ========================================
 * Tüm form gönderimlerini AJAX'a çeviren merkezi sistem
 */

// ============================================
// 1. GLOBAL FETCH FONKSİYONU
// ============================================
async function fetchData(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
        ...options
    };

    try {
        const response = await fetch(url, defaultOptions);
        const data = await response.json();
        return { success: true, data, status: response.status };
    } catch (error) {
        console.error('Fetch Error:', error);
        return { success: false, error: error.message };
    }
}

// ============================================
// 2. LOADING SPINNER YÖNETİMİ
// ============================================
function showLoading(button) {
    if (!button) return;
    
    // Orijinal metni sakla
    button.dataset.originalText = button.innerHTML;
    
    // Spinner ekle
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Yükleniyor...';
    button.disabled = true;
    button.style.opacity = '0.6';
    button.style.cursor = 'not-allowed';
}

function hideLoading(button) {
    if (!button) return;
    
    // Orijinal metni geri yükle
    button.innerHTML = button.dataset.originalText || button.innerHTML;
    button.disabled = false;
    button.style.opacity = '1';
    button.style.cursor = 'pointer';
}

// ============================================
// 3. FORM HIJACKER (Tüm Formları Yakala)
// ============================================
function hijackForms() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Zaten hijack edildiyse tekrar ekleme
        if (form.dataset.hijacked === 'true') return;
        
        form.addEventListener('submit', async function(e) {
            e.preventDefault(); // ⚠️ KRİTİK: Sayfa yenilemeyi engelle
            e.stopPropagation();
            
            const formData = new FormData(form);
            const submitButton = form.querySelector('button[type="submit"]');
            const formAction = form.getAttribute('action') || window.location.pathname;
            const formMethod = form.getAttribute('method') || 'POST';
            
            // Loading state başlat
            showLoading(submitButton);
            
            // FormData'yı JSON'a çevir
            const jsonData = {};
            formData.forEach((value, key) => {
                jsonData[key] = value;
            });
            
            // AJAX isteği gönder
            const result = await fetchData(formAction, {
                method: formMethod,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(jsonData)
            });
            
            // Loading state bitir
            hideLoading(submitButton);
            
            // Sonucu işle
            if (result.success && result.data) {
                handleFormResponse(result.data, form);
            } else {
                showNotification('Hata: ' + (result.error || 'Bilinmeyen hata'), 'error');
            }
        });
        
        // İşaretleme: Bu form artık hijack edildi
        form.dataset.hijacked = 'true';
    });
}

// ============================================
// 4. RESPONSE İŞLEYİCİ
// ============================================
function handleFormResponse(data, form) {
    if (data.success) {
        // Başarılı işlem
        showNotification(data.message || 'İşlem başarılı!', 'success');
        
        // Eğer harita verisi döndüyse güncelle
        if (data.chart_data) {
            updateChart(data.chart_data);
        }
        
        // Eğer rapor verisi döndüyse güncelle
        if (data.report) {
            updateReport(data.report);
        }
        
        // Eğer redirect URL'i döndüyse, o tab'a geç (sayfa yenilemeden)
        if (data.redirect_tab) {
            switchTab(data.redirect_tab);
        }
        
        // Eğer liste güncellenmesi gerekiyorsa
        if (data.update_list) {
            refreshActiveChartsList();
        }
        
    } else {
        // Hata durumu
        showNotification(data.error || 'İşlem başarısız!', 'error');
    }
}

// ============================================
// 5. BİLDİRİM SİSTEMİ (Toast)
// ============================================
function showNotification(message, type = 'info') {
    // Mevcut bildirimleri temizle
    const existingToast = document.querySelector('.ajax-toast');
    if (existingToast) existingToast.remove();
    
    // Yeni bildirim oluştur
    const toast = document.createElement('div');
    toast.className = `ajax-toast ajax-toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    // Animasyonlu giriş
    setTimeout(() => toast.classList.add('ajax-toast-show'), 10);
    
    // 3 saniye sonra kaldır
    setTimeout(() => {
        toast.classList.remove('ajax-toast-show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============================================
// 6. HARİTA GÜNCELLEME
// ============================================
function updateChart(chartData) {
    // SVG'yi temizle ve yeniden çiz
    const svg = document.getElementById('astroChart');
    if (svg && chartData) {
        // Mevcut tüm çizimleri temizle
        while (svg.firstChild) {
            svg.removeChild(svg.firstChild);
        }
        
        // Global chartData'yı güncelle
        if (typeof window.chartData !== 'undefined') {
            window.chartData = chartData;
        }
        
        // Çizim fonksiyonlarını çağır (layout.html'deki fonksiyonlar)
        if (typeof drawZodiac === 'function') drawZodiac();
        if (typeof drawAllPlanets === 'function') drawAllPlanets();
    }
}

// ============================================
// 7. RAPOR GÜNCELLEME
// ============================================
function updateReport(reportHtml) {
    const reportContainer = document.getElementById('hesaplama_raporu');
    if (reportContainer) {
        reportContainer.innerHTML = reportHtml;
    }
}

// ============================================
// 8. TAB DEĞİŞTİRME (Sayfa Yenilemeden)
// ============================================
function switchTab(tabName) {
    // Tüm tab içeriklerini gizle
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    
    // İlgili tab'ı göster
    const targetTab = document.getElementById(tabName);
    if (targetTab) {
        targetTab.style.display = 'block';
    }
    
    // Tab butonlarını güncelle
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('href')?.includes(tabName)) {
            btn.classList.add('active');
        }
    });
}

// ============================================
// 9. AKTİF HARİTALAR LİSTESİNİ YENİLE
// ============================================
async function refreshActiveChartsList() {
    const result = await fetchData('/api/get_active_charts');
    if (result.success && result.data.charts) {
        const listContainer = document.querySelector('.synastry-list');
        if (listContainer) {
            listContainer.innerHTML = result.data.charts.map((chart, index) => `
                <div class="chart-list-item" onclick="loadChartQuickAjax(${index})">
                    <span class="chart-list-name">${chart.name}</span>
                    <span class="chart-list-date">
                        <i class="far fa-calendar-alt"></i> 
                        ${chart.day}.${chart.month}.${chart.year}
                    </span>
                    <span class="chart-list-type">${chart.type || 'natal'}</span>
                </div>
            `).join('');
        }
    }
}

// ============================================
// 10. HARITA HIZLI YÜKLEME (AJAX)
// ============================================
async function loadChartQuickAjax(index) {
    const result = await fetchData(`/api/load_chart/${index}`);
    if (result.success && result.data.chart_data) {
        updateChart(result.data.chart_data);
        showNotification('Harita yüklendi: ' + result.data.chart_info.name, 'success');
    }
}

// ============================================
// 11. SAYFA YÜKLENME - OTOMATİK BAŞLATMA
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Zero-Refresh Policy Aktif!');
    
    // Tüm formları hijack et
    hijackForms();
    
    // Tab linklerin sayfa yenilemesini engelle
    document.querySelectorAll('.tab-button').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const href = this.getAttribute('href');
            const tabName = href.split('tab=')[1];
            if (tabName) {
                switchTab(tabName);
                // URL'yi güncelle (sayfa yenilemeden)
                history.pushState({}, '', href);
            }
        });
    });
    
    // Dinamik içerik değişikliklerini izle (MutationObserver)
    const observer = new MutationObserver(function(mutations) {
        hijackForms(); // Yeni eklenen formları da hijack et
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});

// ============================================
// 12. ÖZEL BUTON İŞLEYİCİLERİ
// ============================================

// Harita silme (AJAX)
async function deleteChartAjax(index) {
    if (!confirm('Bu haritayı silmek istediğinize emin misiniz?')) return;
    
    const result = await fetchData(`/delete_active_chart/${index}`, { method: 'POST' });
    if (result.success) {
        showNotification('Harita silindi', 'success');
        refreshActiveChartsList();
    }
}

// Konum arama (AJAX)
async function searchLocationAjax(cityName) {
    showNotification('Konum aranıyor...', 'info');
    
    const result = await fetchData('/api/search_location', {
        method: 'POST',
        body: JSON.stringify({ city: cityName })
    });
    
    if (result.success && result.data.results) {
        return result.data.results;
    }
    return [];
}
