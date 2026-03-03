/**
 * ========================================
 * ASTRO CHART AJAX MANAGER
 * Sayfa Yenilenmeden Harita Yönetimi
 * ========================================
 */

// Global ChartData - Tüm harita verileri burada
window.chartData = null;

// ============================================
// 1. HARİTA ÇİZİM FONKSİYONLARI
// ============================================

/**
 * Haritayı tamamen yeniden çizer
 * @param {Object} newChartData - Yeni harita verisi
 */
function updateChart(newChartData) {
    if (!newChartData) {
        console.error('❌ Harita verisi boş!');
        return;
    }

    console.log('🎨 Harita güncelleniyor...', newChartData);
    
    // Global chartData'yı güncelle
    window.chartData = newChartData;
    
    // SVG'yi temizle
    const svg = document.getElementById('astroChart');
    if (!svg) {
        console.error('❌ SVG element bulunamadı!');
        return;
    }
    
    // Tüm çocukları temizle
    while (svg.firstChild) {
        svg.removeChild(svg.firstChild);
    }
    
    // Yeniden çiz
    try {
        if (typeof drawZodiac === 'function') {
            drawZodiac();
        }
        if (typeof drawAllPlanets === 'function') {
            drawAllPlanets();
        }
        console.log('✅ Harita başarıyla güncellendi!');
    } catch (error) {
        console.error('❌ Harita çizim hatası:', error);
    }
}

/**
 * Harita bilgi kutusunu günceller
 */
function updateChartInfo(chartInfo) {
    const infoOverlay = document.querySelector('.chart-info-overlay');
    if (!infoOverlay || !chartInfo) return;
    
    const isSynastry = chartInfo.type === 'synastry' || chartInfo.type === 'composite';
    
    if (isSynastry && chartInfo.natal_meta_1 && chartInfo.natal_meta_2) {
        infoOverlay.innerHTML = `
            <div class="chart-info-name-row">
                <span>${chartInfo.natal_meta_1.name}</span>
                <span style="color: #fbbf24; font-weight:300; margin: 0 4px;">&</span>
                <span>${chartInfo.natal_meta_2.name}</span>
            </div>
            <div class="chart-type-label">${chartInfo.type.toUpperCase()}</div>
            <div class="chart-info-row">
                <i class="fas fa-user person-icon"></i>
                <span>1: ${chartInfo.natal_meta_1.day}.${chartInfo.natal_meta_1.month}.${chartInfo.natal_meta_1.year}</span>
            </div>
            <div class="chart-info-row">
                <i class="fas fa-user-friends person-icon"></i>
                <span>2: ${chartInfo.natal_meta_2.day}.${chartInfo.natal_meta_2.month}.${chartInfo.natal_meta_2.year}</span>
            </div>
        `;
    } else {
        const locationName = chartInfo.location_name ? chartInfo.location_name.split(',').slice(0, 2).join(',') : 'Konum Belirsiz';
        infoOverlay.innerHTML = `
            <div class="chart-info-name-row">${chartInfo.name}</div>
            <div class="chart-type-label">${(chartInfo.type || 'NATAL').toUpperCase()}</div>
            <div class="chart-info-row">
                <i class="far fa-calendar-alt"></i>
                <span>${chartInfo.day}.${chartInfo.month}.${chartInfo.year} ${String(chartInfo.hour).padStart(2, '0')}:${String(chartInfo.minute).padStart(2, '0')}</span>
            </div>
            <div class="chart-info-row">
                <i class="fas fa-map-marker-alt"></i>
                <span>${locationName}</span>
            </div>
            <div class="chart-info-row">
                <i class="fas fa-globe"></i>
                <span>${chartInfo.zodiac_type || 'Tropikal'} | UTC ${chartInfo.tz_offset}</span>
            </div>
        `;
    }
}

// ============================================
// 2. AKTİF HARİTA YÜKLEME (AJAX)
// ============================================

/**
 * Aktif haritayı AJAX ile yükler
 * @param {number} index - Harita indeksi
 */
async function loadChartAjax(index) {
    console.log('📡 Harita yükleniyor:', index);
    
    try {
        const response = await fetch(`/api/load_chart/${index}`);
        const data = await response.json();
        
        if (data.success && data.chart_data) {
            // Haritayı güncelle
            updateChart(data.chart_data);
            
            // Bilgi kutusunu güncelle
            updateChartInfo(data.chart_info);
            
            // Liste öğelerini vurgula
            highlightActiveChart(index);
            
            // Başarı bildirimi
            showNotification(`✅ ${data.chart_info.name} yüklendi`, 'success');
        } else {
            showNotification('❌ Harita yüklenemedi: ' + (data.error || 'Bilinmeyen hata'), 'error');
        }
    } catch (error) {
        console.error('❌ AJAX Hatası:', error);
        showNotification('❌ Bağlantı hatası!', 'error');
    }
}

/**
 * Aktif haritayı listede vurgular
 */
function highlightActiveChart(index) {
    document.querySelectorAll('.chart-list-item').forEach((item, idx) => {
        if (idx === index) {
            item.classList.add('selected');
        } else {
            item.classList.remove('selected');
        }
    });
}

// ============================================
// 3. FORM GÖNDERME (AJAX)
// ============================================

/**
 * Natal form gönderimi
 */
async function submitNatalFormAjax(formData) {
    console.log('📤 Natal form gönderiliyor...');
    
    try {
        const response = await fetch('/api/calculate_natal', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(Object.fromEntries(formData))
        });
        
        const data = await response.json();
        
        if (data.success && data.chart_data) {
            // Haritayı güncelle
            updateChart(data.chart_data);
            
            // Bilgi kutusunu güncelle
            updateChartInfo(data.chart_info);
            
            // Aktif listeyi yenile
            refreshActiveChartsList();
            
            // Aktif tab'a geç
            switchTab('aktif');
            
            showNotification('✅ Harita hesaplandı!', 'success');
        } else {
            showNotification('❌ ' + (data.error || 'Hesaplama hatası'), 'error');
        }
    } catch (error) {
        console.error('❌ Form gönderim hatası:', error);
        showNotification('❌ Bağlantı hatası!', 'error');
    }
}

// ============================================
// 4. AKTİF LİSTE YENİLEME
// ============================================

/**
 * Aktif haritalar listesini yeniler
 */
async function refreshActiveChartsList() {
    try {
        const response = await fetch('/api/get_active_charts');
        const data = await response.json();
        
        if (data.success && data.charts) {
            const listContainer = document.querySelector('.synastry-list');
            if (!listContainer) return;
            
            listContainer.innerHTML = data.charts.map((chart, index) => `
                <div class="chart-list-item" onclick="loadChartAjax(${index})" 
                     oncontextmenu="showContextMenu(event, ${index}); return false;">
                    <span class="chart-list-name">${chart.name}</span>
                    <span class="chart-list-date">
                        <i class="far fa-calendar-alt"></i> 
                        ${chart.day}.${chart.month}.${chart.year}
                    </span>
                    <span class="chart-list-type">${chart.type || 'natal'}</span>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('❌ Liste yenileme hatası:', error);
    }
}

// ============================================
// 5. BİLDİRİM SİSTEMİ
// ============================================

function showNotification(message, type = 'info') {
    const existingToast = document.querySelector('.ajax-toast');
    if (existingToast) existingToast.remove();
    
    const toast = document.createElement('div');
    toast.className = `ajax-toast ajax-toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('ajax-toast-show'), 10);
    setTimeout(() => {
        toast.classList.remove('ajax-toast-show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============================================
// 6. TAB DEĞIŞTIRME
// ============================================

function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    
    const targetTab = document.getElementById(tabName);
    if (targetTab) {
        targetTab.style.display = 'block';
    }
    
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('href')?.includes(tabName)) {
            btn.classList.add('active');
        }
    });
    
    // URL'yi güncelle (sayfa yenilemeden)
    history.pushState({}, '', `/?tab=${tabName}`);
}

// ============================================
// 7. SAYFA YÜKLENDİĞİNDE
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Chart AJAX Manager yüklendi!');
    
    // Natal formu hijack et
    const natalForm = document.getElementById('natalForm');
    if (natalForm) {
        natalForm.addEventListener('submit', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const formData = new FormData(natalForm);
            submitNatalFormAjax(formData);
        });
        console.log('✅ Natal form AJAX moduna alındı');
    }
    
    // Tab linkleri hijack et
    document.querySelectorAll('.tab-button').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const href = this.getAttribute('href');
            const tabName = href.split('tab=')[1];
            if (tabName) {
                switchTab(tabName);
            }
        });
    });
    
    console.log('✅ Tüm sistemler hazır - Sayfa yenilenmeyecek!');
});

// Global fonksiyonları pencereye ekle
window.loadChartAjax = loadChartAjax;
window.updateChart = updateChart;
window.refreshActiveChartsList = refreshActiveChartsList;
window.showNotification = showNotification;
window.switchTab = switchTab;
