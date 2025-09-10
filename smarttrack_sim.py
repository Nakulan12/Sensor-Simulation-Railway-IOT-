# smarttrack_virtual_hw_led_emoji.py
import streamlit as st
import numpy as np
import time, random
import matplotlib.pyplot as plt

st.set_page_config(page_title="SmartTrack Virtual Node", layout="wide")
st.title("SmartTrack — Virtual Hardware Node (Simulation Prototype)")

# ---------------- LEFT PANEL ---------------- #
left, right = st.columns([1,2])
with left:
    st.markdown("### Virtual Anchor Node")
    st.markdown("**Node ID:** ANCHOR-001")
    st.markdown("**GPS:** 11.0100, 76.9500")
    st.markdown("**Edge CPU:** Virtual ESP32 / RPi Zero")
    st.markdown("**Power:** Solar + LiFePO4 (simulated)")
    st.markdown("---")

    # Simulation controls
    trigger_event = st.button("Trigger Crack Event")
    sim_mode = st.selectbox("Auto Mode", ["Idle background", "Periodic crack every 10s", "Manual only"])
    severity_override = st.selectbox("Force severity (optional)", ["Auto", "No Crack", "Minor", "Major", "Critical"])
    st.markdown("---")

    # LED placeholders
    st.markdown("#### Device Status LEDs")
    led_col1, led_col2, led_col3 = st.columns(3)
    g_ph = led_col1.empty(); y_ph = led_col2.empty(); r_ph = led_col3.empty()

    st.markdown("#### Sensor Notes")
    st.text("AE: Acoustic emission → crack energy bursts\n"
            "Accel: MEMS vibration → impact + resonance\n"
            "GW-UT: Guided-wave ultrasonic → echo delay\n"
            "Temp: Context (not shown in demo)")

# ---------------- RIGHT PANEL ---------------- #
with right:
    st.markdown("### Sensor Waveforms & On-Edge AI")
    ae_plot = st.empty(); accel_plot = st.empty(); gw_plot = st.empty()
    st.markdown("---")
    clf_box = st.empty()
    json_box = st.empty()

# ---------------- SENSOR WAVEFORM SIM ---------------- #
def gen_waveform(kind, severity):
    t = np.linspace(0,1,800)
    noise = 0.01*np.random.randn(len(t))

    if kind == "AE":
        base = 0.02*np.sin(2*np.pi*60*t) + noise
        if severity == "Minor": sig = base + 0.15*np.exp(-150*(t-0.5)**2)
        elif severity == "Major": sig = base + 0.5*np.exp(-80*(t-0.5)**2)
        elif severity == "Critical": sig = base + 1.0*np.exp(-40*(t-0.5)**2)
        else: sig = base
    elif kind == "Accel":
        base = 0.02*np.sin(2*np.pi*12*t) + 0.005*np.random.randn(len(t))
        if severity == "Minor": sig = base + 0.12*np.exp(-200*(t-0.5)**2)
        elif severity == "Major": sig = base + 0.35*np.exp(-100*(t-0.5)**2)
        elif severity == "Critical": sig = base + 0.8*np.exp(-60*(t-0.5)**2)
        else: sig = base
    else:  # Guided-Wave UT
        base = 0.01*np.sin(2*np.pi*150*t) + noise
        if severity == "Minor": sig = base + 0.08*np.exp(-300*(t-0.7)**2)
        elif severity == "Major": sig = base + 0.3*np.exp(-150*(t-0.6)**2)
        elif severity == "Critical": sig = base + 0.8*np.exp(-90*(t-0.55)**2)
        else: sig = base
    return t, sig

# ---------------- SEVERITY DECISION ---------------- #
def decide_severity(auto_mode, manual_override, triggered):
    if manual_override != "Auto":
        return manual_override
    if auto_mode == "Manual only" and not triggered:
        return "No Crack"
    if auto_mode == "Periodic crack every 10s":
        sec = int(time.time())
        if sec % 10 == 0:
            return random.choice(["Minor","Major","Critical"])
        else:
            return "No Crack"
    if triggered:
        return random.choice(["Minor","Major","Critical"])
    return "No Crack"

triggered = trigger_event
severity = decide_severity(sim_mode, severity_override, triggered)

# ---------------- PLOT ---------------- #
def plot_waveform(t, sig, title):
    fig, ax = plt.subplots(figsize=(6,1.6))
    ax.plot(t, sig, lw=1)
    ax.set_title(title, fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])
    fig.tight_layout()
    return fig

t_a, ae = gen_waveform("AE", severity)
t_b, acc = gen_waveform("Accel", severity)
t_c, gw = gen_waveform("GW", severity)

ae_plot.pyplot(plot_waveform(t_a, ae, f"AE (Acoustic Emission) — {severity}"))
accel_plot.pyplot(plot_waveform(t_b, acc, f"Accelerometer Array — {severity}"))
gw_plot.pyplot(plot_waveform(t_c, gw, f"Guided-Wave UT Echo — {severity}"))

# ---------------- CLASSIFIER ---------------- #
if severity == "No Crack": label, conf = "No Crack", round(random.uniform(0.9,0.99),2)
elif severity == "Minor": label, conf = "Minor", round(random.uniform(0.7,0.88),2)
elif severity == "Major": label, conf = "Major", round(random.uniform(0.85,0.95),2)
else: label, conf = "Critical", round(random.uniform(0.9,0.98),2)

clf_box.markdown(f"### On-Edge Classifier\n**Prediction:** {label}\n\n**Confidence:** {conf}")

# ---------------- LED STATUS (EMOJIS ONLY) ---------------- #
if label == "No Crack":
    g_ph.success("🟢 Green ON")
    y_ph.write("🟡 Yellow OFF")
    r_ph.write("🔴 Red OFF")
elif label == "Minor":
    g_ph.write("🟢 Green OFF")
    y_ph.warning("🟡 Yellow ON")
    r_ph.write("🔴 Red OFF")
else:
    g_ph.write("🟢 Green OFF")
    y_ph.write("🟡 Yellow OFF")
    r_ph.error("🔴 Red ON")

# ---------------- JSON ALERT ---------------- #
alert = {
    "node_id":"ANCHOR-001",
    "gps":"11.0100,76.9500",
    "severity": label,
    "confidence": conf,
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "waveform_samples": len(ae)
}
json_box.json(alert)

if label != "No Crack":
    st.warning("Mock Alert sent: Dashboard + SMS/Email notification")

st.caption("Trigger a manual event or use Auto mode to simulate realistic sensor bursts for AE, Accel, and GW-UT sensors.")
