const NOTE_ON = 0x90;
const NOTE_OFF = 0x80;

function midiToFreq(note) {
  return 440 * Math.pow(2, (note - 69) / 12);
}

function render({ model, el }) {
  const container = document.createElement('div');
  container.className = 'midi-container';

  const select = document.createElement('select');
  select.className = 'midi-select';

  const status = document.createElement('span');
  status.className = 'midi-status';
  status.textContent = 'requesting access…';

  container.appendChild(select);
  container.appendChild(status);
  el.appendChild(container);

  let activeInput = null;
  let midiAccess = null;

  function onMessage(e) {
    const [cmd, note, velocity] = e.data;
    const type = cmd & 0xf0;

    if (type === NOTE_ON && velocity > 0) {
      model.set('note', note);
      model.set('velocity', velocity);
      model.set('frequency', midiToFreq(note));
      model.set('gate', true);
      model.save_changes();
    } else if (type === NOTE_OFF || (type === NOTE_ON && velocity === 0)) {
      if (note === model.get('note')) {
        model.set('gate', false);
        model.set('velocity', 0);
        model.save_changes();
      }
    }
  }

  function bindInput(input) {
    if (activeInput) activeInput.onmidimessage = null;
    activeInput = input;
    if (input) {
      input.onmidimessage = onMessage;
      status.textContent = input.name || 'connected';
      model.set('device_name', input.name || 'unknown');
      model.set('connected', true);
    } else {
      status.textContent = 'none selected';
      model.set('device_name', '');
      model.set('connected', false);
    }
    model.save_changes();
  }

  function refreshDeviceList() {
    if (!midiAccess) return;
    const prev = select.value;
    select.innerHTML = '';

    const none = document.createElement('option');
    none.value = '';
    none.textContent = '— select MIDI device —';
    select.appendChild(none);

    for (const [id, input] of midiAccess.inputs) {
      const opt = document.createElement('option');
      opt.value = id;
      opt.textContent = input.name || id;
      select.appendChild(opt);
    }

    // restore previous selection if still available, else keep blank
    if (prev && midiAccess.inputs.has(prev)) {
      select.value = prev;
    } else {
      select.value = '';
      bindInput(null);
    }
  }

  select.addEventListener('change', () => {
    const id = select.value;
    if (id && midiAccess && midiAccess.inputs.has(id)) {
      bindInput(midiAccess.inputs.get(id));
    } else {
      bindInput(null);
    }
  });

  if (navigator.requestMIDIAccess) {
    navigator
      .requestMIDIAccess()
      .then((access) => {
        midiAccess = access;
        refreshDeviceList();
        access.onstatechange = () => refreshDeviceList();
      })
      .catch((err) => {
        status.textContent = err.message;
        model.set('connected', false);
        model.save_changes();
      });
  } else {
    status.textContent = 'Web MIDI not supported';
    model.set('connected', false);
    model.save_changes();
  }
}

export default { render };
