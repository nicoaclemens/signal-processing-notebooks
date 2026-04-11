# used by:
import numpy as np
import ipywidgets as widgets
from utils.signals import WAVE_FUNCS
from utils.ui import section, plot_waveform_and_fft
from widget import AudioWidget
from widget.knob_widget import KnobWidget
from widget.midi_input_widget import MidiInputWidget
from widget.switch_widget import SwitchWidget

# --- Minimoog oscillator constants ---

_RANGE_LABELS = ["LO", "32'", "16'", "8'", "4'", "2'"]
# LO = sub-audio (~1/16 of base), then each step doubles frequency
_RANGE_MULT = [1 / 16, 1 / 4, 1 / 2, 1, 2, 4]

_WAVE_LABELS = ["\u25b3", "\u25b3/\u2571", "Ramp", "Sq", "Wide", "Narrow"]
# Web Audio types: triangle, custom sharktooth, sawtooth, square + PWM
_WAVE_KEYS = ["triangle", "sharktooth", "sawtooth", "square", "pwm25", "pwm12"]

# Map to Web Audio native types where possible; others handled as custom periodic waves
_WEB_AUDIO_TYPES = {
    "triangle": "triangle",
    "sharktooth": "sharktooth",
    "sawtooth": "sawtooth",
    "square": "square",
    "pwm25": "pwm25",
    "pwm12": "pwm12",
}

N_PERIOD = 512


def create_synth_ui(f_init=440):
    # ========== CONTROLLERS SECTION ==========

    tune_knob = KnobWidget(
        value=0,
        default_value=0,
        min=-2,
        max=2,
        step=0.01,
        label="Tune",
        unit="st",
        readout_format=".2f",
        color="#f7a16a",
        size=60,
    )
    glide_knob = KnobWidget(
        value=0,
        default_value=0,
        min=0,
        max=10,
        step=0.1,
        label="Glide",
        readout_format=".1f",
        color="#f7a16a",
        size=60,
    )
    mod_mix_knob = KnobWidget(
        value=0,
        default_value=0,
        min=0,
        max=10,
        step=0.1,
        label="Mod Mix",
        readout_format=".1f",
        color="#f7a16a",
        size=60,
    )

    # Gray switches for modulation source selection
    mod_source_switch = SwitchWidget(
        value=False,
        label="Mod Src",
        option_labels=["Osc 3", "Flt EG"],
        color="#888",
        orientation="horizontal",
    )
    mod_type_switch = SwitchWidget(
        value=False,
        label="Mod Type",
        option_labels=["Noise", "LFO"],
        color="#888",
        orientation="horizontal",
    )

    # ========== OSCILLATOR BANK SECTION ==========

    # Orange switch: oscillator modulation on/off (spans border)
    osc_mod_switch = SwitchWidget(
        value=False,
        label="Osc Mod",
        option_labels=["Off", "On"],
        color="#f7a16a",
        orientation="horizontal",
    )

    def _make_osc_controls(n, has_detune=False):
        """Create range + waveform knobs (+ detune if osc 2 or 3)."""
        range_knob = KnobWidget(
            mode="discrete",
            options=_RANGE_LABELS,
            value=3,  # default = 8'
            label=f"Osc {n} Range",
            color="#f7a16a",
        )
        wave_knob = KnobWidget(
            mode="discrete",
            options=_WAVE_LABELS,
            value=0,  # default = triangle
            label=f"Osc {n} Wave",
            color="#f7a16a",
        )
        detune_knob = None
        if has_detune:
            detune_knob = KnobWidget(
                value=0,
                default_value=0,
                min=-7,
                max=7,
                step=0.01,
                label=f"Osc {n} Tune",
                unit="st",
                readout_format=".2f",
                color="#f7a16a",
                size=60,
            )
        return range_knob, wave_knob, detune_knob

    osc1_range, osc1_wave, _ = _make_osc_controls(1)
    osc2_range, osc2_wave, osc2_tune = _make_osc_controls(2, has_detune=True)
    osc3_range, osc3_wave, osc3_tune = _make_osc_controls(3, has_detune=True)

    # Osc 3 keyboard control (off = fixed frequency)
    osc3_kb_switch = SwitchWidget(
        value=True,
        label="Osc 3 Kbd",
        option_labels=["Off", "On"],
        color="#f7a16a",
        orientation="vertical",
    )

    # ========== MIXER SECTION ==========

    def _make_mixer_channel(n):
        vol = KnobWidget(
            value=10,
            default_value=10,
            min=0,
            max=10,
            step=0.1,
            label=f"Osc {n} Vol",
            readout_format=".1f",
            color="#5de8a0",
            size=60,
        )
        sw = SwitchWidget(
            value=True,
            label=f"Osc {n}",
            option_labels=["Off", "On"],
            color="#5de8a0",
            orientation="horizontal",
        )
        return vol, sw

    mix1_vol, mix1_sw = _make_mixer_channel(1)
    mix2_vol, mix2_sw = _make_mixer_channel(2)
    mix3_vol, mix3_sw = _make_mixer_channel(3)

    noise_sw = SwitchWidget(
        value=False,
        label="Noise",
        option_labels=["Off", "On"],
        color="#5de8a0",
        orientation="horizontal",
    )
    noise_vol = KnobWidget(
        value=0,
        default_value=0,
        min=0,
        max=1,
        step=0.01,
        label="Noise Vol",
        readout_format=".2f",
        color="#5de8a0",
        size=60,
    )
    noise_type_sw = SwitchWidget(
        value=False,
        label="Noise Type",
        option_labels=["White", "Pink"],
        color="#5de8a0",
        orientation="vertical",
    )

    # ========== FILTER SECTION ==========

    filter_mod_sw = SwitchWidget(
        value=False,
        label="Filter Mod",
        option_labels=["Off", "On"],
        color="#f7a16a",
        orientation="vertical",
    )
    filter_kb1_sw = SwitchWidget(
        value=False,
        label="Kbd Ctrl 1",
        option_labels=["Off", "On"],
        color="#f7a16a",
        orientation="vertical",
    )
    filter_kb2_sw = SwitchWidget(
        value=False,
        label="Kbd Ctrl 2",
        option_labels=["Off", "On"],
        color="#f7a16a",
        orientation="vertical",
    )

    cutoff_knob = KnobWidget(
        value=0,
        default_value=0,
        min=-4,
        max=4,
        step=0.01,
        label="Cutoff",
        readout_format=".2f",
        color="#f7a16a",
        size=60,
    )
    emphasis_knob = KnobWidget(
        value=0,
        default_value=0,
        min=0,
        max=10,
        step=0.1,
        label="Emphasis",
        readout_format=".1f",
        color="#f7a16a",
        size=60,
    )
    contour_knob = KnobWidget(
        value=0,
        default_value=0,
        min=0,
        max=10,
        step=0.1,
        label="Contour",
        readout_format=".1f",
        color="#f7a16a",
        size=60,
    )
    filter_attack = KnobWidget(
        value=0.01,
        default_value=0.01,
        min=0.01,
        max=10,
        step=0.01,
        label="Attack",
        unit="s",
        readout_format=".2f",
        color="#f7a16a",
        size=60,
    )
    filter_decay = KnobWidget(
        value=0.01,
        default_value=0.01,
        min=0.01,
        max=10,
        step=0.01,
        label="Decay",
        unit="s",
        readout_format=".2f",
        color="#f7a16a",
        size=60,
    )
    filter_sustain = KnobWidget(
        value=10,
        default_value=10,
        min=0,
        max=10,
        step=0.1,
        label="Sustain",
        readout_format=".1f",
        color="#f7a16a",
        size=60,
    )

    # ========== LOUDNESS CONTOUR SECTION ==========

    loud_attack = KnobWidget(
        value=0.01,
        default_value=0.01,
        min=0.01,
        max=10,
        step=0.01,
        label="Attack",
        unit="s",
        readout_format=".2f",
        color="#f7a16a",
        size=60,
    )
    loud_decay = KnobWidget(
        value=0.01,
        default_value=0.01,
        min=0.01,
        max=10,
        step=0.01,
        label="Decay",
        unit="s",
        readout_format=".2f",
        color="#f7a16a",
        size=60,
    )
    loud_sustain = KnobWidget(
        value=10,
        default_value=10,
        min=0,
        max=10,
        step=0.1,
        label="Sustain",
        readout_format=".1f",
        color="#f7a16a",
        size=60,
    )

    # ========== OUTPUT SECTION ==========

    vol_knob = KnobWidget(
        value=0.5,
        default_value=0.5,
        min=0.0,
        max=1.0,
        step=0.01,
        label="Volume",
        readout_format=".2f",
        color="#5de8a0",
        size=60,
    )
    main_out_sw = SwitchWidget(
        value=True,
        label="Main Out",
        option_labels=["Off", "On"],
        color="#5de8a0",
        orientation="horizontal",
    )
    ref_tone_sw = SwitchWidget(
        value=False,
        label="A=440",
        option_labels=["Off", "On"],
        color="#5de8a0",
        orientation="horizontal",
    )

    # ========== LFO CONTROLLER SECTION ==========

    lfo_rate_knob = KnobWidget(
        value=5,
        default_value=5,
        min=0.1,
        max=30,
        step=0.1,
        label="LFO Rate",
        unit="Hz",
        readout_format=".1f",
        color="#f7a16a",
        size=60,
    )
    glide_sw = SwitchWidget(
        value=False,
        label="Glide",
        option_labels=["Off", "On"],
        color="#ddd",
        orientation="horizontal",
    )
    decay_sw = SwitchWidget(
        value=False,
        label="Decay",
        option_labels=["Off", "On"],
        color="#ddd",
        orientation="horizontal",
    )
    pitch_wheel = widgets.FloatSlider(
        value=0,
        min=-1,
        max=1,
        step=0.01,
        description="Pitch",
        orientation="vertical",
        readout=False,
        style={"handle_color": "#f7a16a"},
        layout=widgets.Layout(height="120px"),
    )
    mod_wheel = widgets.FloatSlider(
        value=0,
        min=0,
        max=1,
        step=0.01,
        description="Mod.",
        orientation="vertical",
        readout=False,
        style={"handle_color": "#f7a16a"},
        layout=widgets.Layout(height="120px"),
    )

    # ========== AUDIO ENGINE ==========

    audio = AudioWidget(
        components=[
            {
                "id": "osc1",
                "label": "Osc 1",
                "oscs": [{"freq": f_init, "gain": 1.0}],
                "enabled": True,
            },
            {
                "id": "osc2",
                "label": "Osc 2",
                "oscs": [{"freq": f_init, "gain": 1.0}],
                "enabled": True,
            },
            {
                "id": "osc3",
                "label": "Osc 3",
                "oscs": [{"freq": f_init, "gain": 1.0}],
                "enabled": True,
            },
        ],
    )

    widgets.jslink((vol_knob, "value"), (audio, "volume"))

    midi = MidiInputWidget()
    widgets.jslink((midi, "frequency"), (audio, "mono_frequency"))

    fft_out = widgets.Output()

    # ========== CALLBACKS ==========

    def _get_wave_key(wave_knob):
        return _WAVE_KEYS[wave_knob.index]

    def _push_osc_config(_change=None):
        audio.osc_config = {
            "osc1": {
                "freq_mult": _RANGE_MULT[osc1_range.index],
                "detune": 0,
                "kb_track": True,
            },
            "osc2": {
                "freq_mult": _RANGE_MULT[osc2_range.index],
                "detune": osc2_tune.value,
                "kb_track": True,
            },
            "osc3": {
                "freq_mult": _RANGE_MULT[osc3_range.index],
                "detune": osc3_tune.value,
                "kb_track": osc3_kb_switch.value,
            },
        }

    def _push_waveforms(_change=None):
        wf = {}
        for osc_id, wave_knob in [
            ("osc1", osc1_wave),
            ("osc2", osc2_wave),
            ("osc3", osc3_wave),
        ]:
            key = _get_wave_key(wave_knob)
            wf[osc_id] = _WEB_AUDIO_TYPES[key]
        audio.waveforms = wf

    def _push_master_tune(_change=None):
        audio.master_tune = tune_knob.value

    def _push_glide(_change=None):
        audio.glide_time = glide_knob.value / 10.0

    def _push_enables(_change=None):
        audio.enables = {
            "osc1": mix1_sw.value,
            "osc2": mix2_sw.value,
            "osc3": mix3_sw.value,
        }

    def _push_mixer_volumes(_change=None):
        audio.mixer_volumes = {
            "osc1": mix1_vol.value / 10.0,
            "osc2": mix2_vol.value / 10.0,
            "osc3": mix3_vol.value / 10.0,
        }

    def _update_plots(freq_override=None):
        freq = freq_override if freq_override else f_init
        plot_waveform_and_fft(fft_out, None, freq, label="synth")

    def _on_midi_freq(change):
        if midi.gate:
            _update_plots(freq_override=change["new"])

    # Observe oscillator bank controls
    for knob in [osc1_range, osc2_range, osc3_range, osc2_tune, osc3_tune]:
        knob.observe(_push_osc_config, "value")
    osc3_kb_switch.observe(_push_osc_config, "value")

    for knob in [osc1_wave, osc2_wave, osc3_wave]:
        knob.observe(_push_waveforms, "value")

    tune_knob.observe(_push_master_tune, "value")
    glide_knob.observe(_push_glide, "value")
    midi.observe(_on_midi_freq, "frequency")

    # Observe mixer controls
    for sw in [mix1_sw, mix2_sw, mix3_sw]:
        sw.observe(_push_enables, "value")
    for knob in [mix1_vol, mix2_vol, mix3_vol]:
        knob.observe(_push_mixer_volumes, "value")

    # Initial push
    _push_osc_config()
    _push_waveforms()
    _push_master_tune()
    _push_glide()
    _push_enables()
    _push_mixer_volumes()
    audio.frequencies = {
        "osc1": [f_init],
        "osc2": [f_init],
        "osc3": [f_init],
    }
    _update_plots()

    # ========== LAYOUT ==========

    controller_knobs = widgets.HBox(
        [tune_knob, glide_knob, mod_mix_knob],
        layout=widgets.Layout(gap="16px"),
    )
    controller_switches = widgets.HBox(
        [mod_source_switch, mod_type_switch],
        layout=widgets.Layout(gap="16px"),
    )
    controllers = widgets.VBox(
        [
            section("Controllers"),
            widgets.HBox(
                [controller_knobs, controller_switches],
                layout=widgets.Layout(gap="24px", align_items="center"),
            ),
        ]
    )

    osc1_row = widgets.HBox(
        [osc1_range, osc1_wave],
        layout=widgets.Layout(gap="12px"),
    )
    osc2_row = widgets.HBox(
        [osc2_range, osc2_wave, osc2_tune],
        layout=widgets.Layout(gap="12px"),
    )
    osc3_row = widgets.HBox(
        [osc3_range, osc3_wave, osc3_tune, osc3_kb_switch],
        layout=widgets.Layout(gap="12px"),
    )

    osc_bank = widgets.VBox(
        [
            section("Oscillator Bank"),
            widgets.HBox(
                [osc_mod_switch],
                layout=widgets.Layout(margin="0 0 4px 0"),
            ),
            section("Oscillator 1"),
            osc1_row,
            section("Oscillator 2"),
            osc2_row,
            section("Oscillator 3"),
            osc3_row,
        ]
    )

    mix1_row = widgets.HBox(
        [mix1_vol, mix1_sw],
        layout=widgets.Layout(gap="12px"),
    )
    mix2_row = widgets.HBox(
        [mix2_vol, mix2_sw],
        layout=widgets.Layout(gap="12px"),
    )
    mix3_row = widgets.HBox(
        [mix3_vol, mix3_sw],
        layout=widgets.Layout(gap="12px"),
    )
    noise_row = widgets.HBox(
        [noise_sw, noise_vol, noise_type_sw],
        layout=widgets.Layout(gap="12px"),
    )
    mixer = widgets.VBox(
        [
            section("Mixer"),
            section("Oscillator 1"),
            mix1_row,
            section("Oscillator 2"),
            mix2_row,
            section("Oscillator 3"),
            mix3_row,
            section("Noise"),
            noise_row,
        ]
    )

    filter_border_switches = widgets.HBox(
        [filter_mod_sw, filter_kb1_sw, filter_kb2_sw],
        layout=widgets.Layout(gap="8px"),
    )
    filter_knobs_top = widgets.HBox(
        [cutoff_knob, emphasis_knob, contour_knob],
        layout=widgets.Layout(gap="12px"),
    )
    filter_knobs_bot = widgets.HBox(
        [filter_attack, filter_decay, filter_sustain],
        layout=widgets.Layout(gap="12px"),
    )
    filter_section = widgets.VBox(
        [
            filter_border_switches,
            section("Filter"),
            filter_knobs_top,
            filter_knobs_bot,
        ]
    )

    loud_knobs = widgets.HBox(
        [loud_attack, loud_decay, loud_sustain],
        layout=widgets.Layout(gap="12px"),
    )
    loudness_section = widgets.VBox([section("Loudness Contour"), loud_knobs])

    modifiers = widgets.VBox(
        [
            section("Modifiers"),
            filter_section,
            loudness_section,
        ]
    )

    output_section = widgets.VBox(
        [section("Output"), vol_knob, main_out_sw, ref_tone_sw]
    )

    lfo_switches = widgets.HBox(
        [glide_sw, decay_sw],
        layout=widgets.Layout(gap="12px"),
    )
    lfo_wheels = widgets.HBox(
        [pitch_wheel, mod_wheel],
        layout=widgets.Layout(gap="16px"),
    )
    lfo_section = widgets.HBox(
        [
            widgets.VBox([section("LFO Controller"), lfo_rate_knob, lfo_switches]),
            lfo_wheels,
        ],
        layout=widgets.Layout(gap="24px", align_items="flex-end"),
    )

    top = widgets.HBox(
        [controllers, osc_bank, mixer, modifiers, output_section],
        layout=widgets.Layout(gap="32px", align_items="flex-start"),
    )

    return widgets.VBox([top, lfo_section, midi, audio, fft_out])
