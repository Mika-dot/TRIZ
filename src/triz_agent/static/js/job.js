(function () {
  const root = document.getElementById('job-root');
  if (!root) return;
  const jobId = root.dataset.jobId;
  const stageContainer = document.getElementById('stages-container');
  const currentStage = document.getElementById('current-stage');
  const progressText = document.getElementById('progress-text');
  const progressFill = document.getElementById('progress-fill');
  const jobStatusText = document.getElementById('job-status-text');
  const jobError = document.getElementById('job-error');
  const jobSuccess = document.getElementById('job-success');
  let redirected = false;

  function escapeHtml(value) {
    return String(value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function renderStage(stage) {
    return `
      <article class="stage-card ${stage.status_hint === 'warning' ? 'warning' : ''}">
        <div class="stage-card-head">
          <div>
            <strong>${escapeHtml(stage.stage_id)}. ${escapeHtml(stage.title)}</strong>
            <div class="muted small">${escapeHtml(stage.block || '')}</div>
          </div>
          <span class="pill ${stage.confidence >= 0.85 ? 'good' : (stage.confidence >= 0.65 ? 'warn' : 'bad')}">${Number(stage.confidence || 0).toFixed(2)}</span>
        </div>
        <p>${escapeHtml(stage.summary || '')}</p>
      </article>
    `;
  }

  function updateJob(data) {
    currentStage.textContent = `${data.current_stage_id || 'Подготовка'} ${data.current_stage_title || ''}`.trim();
    progressText.textContent = `${data.stage_index}/${data.total_stages}`;
    progressFill.style.width = `${data.progress_percent}%`;

    if (data.status === 'failed') {
      jobStatusText.textContent = 'Выполнение остановлено';
      jobError.textContent = data.error || 'Неизвестная ошибка';
      jobError.classList.remove('hidden');
    } else if (data.status === 'completed') {
      jobStatusText.textContent = 'Пайплайн завершён';
      const runId = data.artifacts && data.artifacts.run_id;
      if (runId) {
        jobSuccess.innerHTML = `Результат готов. Переход на страницу запуска <strong>${escapeHtml(runId)}</strong>…`;
        jobSuccess.classList.remove('hidden');
        if (!redirected) {
          redirected = true;
          setTimeout(() => { window.location.href = `/runs/${encodeURIComponent(runId)}`; }, 800);
        }
      }
    } else {
      jobStatusText.textContent = 'Пайплайн выполняется…';
    }

    stageContainer.innerHTML = data.results.map(renderStage).join('');
  }

  async function poll() {
    try {
      const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}`);
      if (!response.ok) {
        throw new Error('Не удалось получить статус задачи');
      }
      const data = await response.json();
      updateJob(data);
      if (data.status === 'queued' || data.status === 'running') {
        setTimeout(poll, 1500);
      }
    } catch (error) {
      jobError.textContent = error.message;
      jobError.classList.remove('hidden');
      setTimeout(poll, 4000);
    }
  }

  poll();
})();
