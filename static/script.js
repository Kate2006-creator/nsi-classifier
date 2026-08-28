async function loadStats() {
    try {
        const response = await fetch('/stats');
        const stats = await response.json();
        
        document.getElementById('totalPositions').textContent = stats.total_positions || 0;
        document.getElementById('coveredPositions').textContent = stats.covered_positions || 0;
        document.getElementById('coveragePercent').textContent = 
            stats.coverage_percent ? stats.coverage_percent.toFixed(1) + '%' : '-';
        document.getElementById('etalonCount').textContent = stats.etalon_count || 0;
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
    }
}

async function loadEtalons() {
    const container = document.getElementById('etalonList');
    
    try {
        const response = await fetch('/etalon');
        const etalons = await response.json();
        
        if (etalons.length === 0) {
            container.innerHTML = '<p class="loading">Нет эталонных записей</p>';
            return;
        }
        
        etalons.sort((a, b) => b.cluster_size - a.cluster_size);
        
        let html = '';
        for (const item of etalons) {
            html += `
                <div class="etalon-item">
                    <span class="name">${item.etalon_name}</span>
                    <span class="size">${item.cluster_size} шт</span>
                </div>
            `;
        }
        container.innerHTML = html;
        
    } catch (error) {
        container.innerHTML = '<p class="loading">Ошибка загрузки эталонов</p>';
        console.error('Ошибка:', error);
    }
}


document.getElementById('classifyForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const input = document.getElementById('positionInput');
    const name = input.value.trim();
    const resultDiv = document.getElementById('result');
    
    if (!name) {
        resultDiv.className = 'result visible error';
        resultDiv.innerHTML = '<p>⚠️ Введите название должности</p>';
        return;
    }
    
    resultDiv.className = 'result visible';
    resultDiv.innerHTML = '<p>Поиск...</p>';
    
    try {
        const response = await fetch(`/classify?name=${encodeURIComponent(name)}`);
        const data = await response.json();
        
        if (data.etalon) {
            resultDiv.className = 'result visible success';
            resultDiv.innerHTML = `
                <div class="position">${data.position}</div>
                <div class="etalon">→ ${data.etalon}</div>
                <div class="cluster">Кластер: ${data.cluster || '—'}</div>
            `;
        } else {
            resultDiv.className = 'result visible error';
            resultDiv.innerHTML = `
                <p>Должность не найдена в эталонном справочнике</p>
                <p style="font-size:14px;color:#7f8c8d;margin-top:8px;">Попробуйте ввести другую должность</p>
            `;
        }
        
    } catch (error) {
        resultDiv.className = 'result visible error';
        resultDiv.innerHTML = `<p>Ошибка: ${error.message}</p>`;
    }
});


document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadEtalons();
});