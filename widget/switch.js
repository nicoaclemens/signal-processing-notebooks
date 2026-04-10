function render({ model, el }) {
  const container = document.createElement('div');
  container.className = 'switch-container';

  const topLabel = document.createElement('div');
  topLabel.className = 'switch-option-label switch-option-top';

  const track = document.createElement('div');
  track.className = 'switch-track';

  const thumb = document.createElement('div');
  thumb.className = 'switch-thumb';

  track.appendChild(thumb);

  const bottomLabel = document.createElement('div');
  bottomLabel.className = 'switch-option-label switch-option-bottom';

  const mainLabel = document.createElement('div');
  mainLabel.className = 'switch-label';

  container.appendChild(topLabel);
  container.appendChild(track);
  container.appendChild(bottomLabel);
  container.appendChild(mainLabel);
  el.appendChild(container);

  function draw() {
    const value = model.get('value');
    const color = model.get('color');
    const orientation = model.get('orientation');
    const labels = model.get('option_labels');

    container.setAttribute('data-orientation', orientation);

    // labels for the two positions
    topLabel.textContent = labels[0] || '';
    bottomLabel.textContent = labels[1] || '';

    // main label
    mainLabel.textContent = model.get('label');

    // track color when on
    track.style.borderColor = value ? color : '';

    // thumb position
    thumb.style.background = color;
    if (value) {
      thumb.classList.add('switch-on');
    } else {
      thumb.classList.remove('switch-on');
    }
  }

  track.addEventListener('click', () => {
    model.set('value', !model.get('value'));
    model.save_changes();
  });

  model.on('change', draw);
  draw();
}

export default { render };
