# KONYA FOOD AND AGRICULTURE UNIVERSITY

# FACULTY OF ENGINEERING AND ARCHITECTURE

# DEPARTMENT OF COMPUTER ENGINEERING

# LIGHTWEIGHT HYBRID INTRUSION DETECTION SYSTEM

# FOR SMALL-SCALE NETWORKS

# PROJECT PROPOSAL

```
Mustafa Emir KAYNAR
&
Şamil KEKLİKOĞLU
```

## 1. General Information

```
Project Title: Lightweight Hybrid Intrusion Detection System for Small-scale Networks
Authors: Mustafa Emir KAYNAR, Şamil KEKLİKOĞLU
Advisor: Prof. Dr. Reza Zare HASSANPOUR
```

## 2. Introduction

In today's interconnected world, network security is a paramount concern. While large
companies invest in sophisticated and enterprise solutions, small-scale networks - such as small
offices, home offices and businesses - often lack the technical knowledge and financial resources
to implement robust solutions for network security.
These small networks are vulnerable to threats, the commercial Intrusion Detection Systems
(IDS) are often too complex and heavyweight for consumer grade hardware that this type of
businesses use. The growing use of end-to-end encryption makes traditional signature and rule
based systems ineffective, since they can no longer inspect packet payloads. This highlights a
crucial research gap, the need for a lightweight solution that can smartly identify new threats and
suspicious patterns within encrypted traffic without causing significant performance impact.

## 3. Problem Statement

Small-scale networks lack real-time, accessible and resource efficient tools to detect common
and novel network intrusions, especially with encrypted traffic being so common nowadays. This
leaves them vulnerable to attacks that can disrupt traffic and compromise sensitive data.
The primary challenge is to develop a hybrid system that combines the strengths of traditional
rule-based detection with the intelligence of machine learning to provide meaningful security
alerts without high cost or performance overhead.

## 4. Aims and Objectives

**Aim:**
To design, develop and evaluate a lightweight, hybrid, real-time network monitoring tool that
detects suspicious traffic patterns, common and novel attacks on a small-scale network.
**Objectives:**

1. Research and select an appropriate, efficient method for capturing network traffic in
   real-time using common libraries (e.g. Wireshark, tcpdump, scapy, pcapy).
2. Develop a packet processing and advanced feature extraction module to create statistical
   flow-based features (e.g. packet size, frequency, flow duration).
3. Design and implement a hybrid detection engine that combines:
   a. A simple, efficient rule-based component for traditional attacks (e.g. port
   scanning).
   b. An unsupervised machine learning model (e.g. Isolation Forest, Autoencoder) to
   detect novel anomalies and behavioural deviations.
4. Investigate and implement techniques for Encrypted Traffic Analysis (ETA) using traffic
   metadata and flow statistics to identify suspicious activity patterns without decryption.
5. Create an interactive web-based dashboard to visualize the output of all our modules.
6. Evaluate the systems effectiveness by analysing its detection accuracy on a controlled test
   network and benchmarking its performance against public IDS datasets like
   CIC-IDS-2017/

## 5. Scope

```
### In Scope
● The system will monitor traffic on a
single network interface.
● Detection will be a hybrid model,
focusing on network-level anomalies
(port scans, floods) and behavioral
anomalies identified by the ML model.
● Analysis of encrypted traffic metadata
(e.g., flow data, packet size/timing) to
infer activity.
● The system will be a detection system,
not a prevention system (it will alert,
not block).
● The dashboard will be an interactive
visualization layer, not a full-featured
SIEM.

### Out of Scope
● Deep Packet Inspection (DPI) for
malicious payloads.
● Direct decryption of encrypted traffic.
● Supervised machine learning models
that require a fully labeled, real-time
dataset (focus is on unsupervised
detection).
● Automated incident response or traffic
blocking.
```

## 6. Methodology and Approach

The project follows an incremental, phase-based development approach (subject to refinement
during implementation)
**Phase 1: Traffic Capture & Feature Extraction**
Implement real-time packet capture using Python libraries (Scapy/pcapy/tcpdump). Extract
flow-based statistical features (packet size, frequency, duration, protocol distribution) suitable for
encrypted traffic analysis.
**Phase 2: Hybrid Detection Engine**
● Tier 1 (Rule-based): Real-time fast detection of known attacks (port scans, DoS,
connection floods)
● Tier 2 (ML-based): Unsupervised anomaly detection for more novel attacks (Contingent
on Tier 1 stability and consumer hardware performance testing)

**Phase 3: Visualization**
Integrate a front-end solution to the project for real-time monitoring and alerts. Most likely using
Grafana/InfluxDB to cut development time from the front-end.
**Phase 4: Evaluation**
Test on CIC-IDS-2017/2018 datasets, measuring detection accuracy (TPR, FPR, F1-score) and
system performance (CPU, RAM, latency).
**Technology Stack (Not final)**
Python 3.11+, NumPy/Pandas, scikit-learn, Grafana, InfluxDB, Docker Compose
**Development Strategy**
Build MVP with Python, implement Tier 1 first, add Tier 2 only if resource-efficient on
consumer hardware. This plan will be adapted based on testing results and technical constraints
encountered during development.

## 7. Expected Outcomes

The primary outcomes of this project will be:

1. A functional prototype of a lightweight, hybrid intrusion detection system.
2. A demonstrated ability to detect both known attacks (via rules) in real-time and novel
   anomalies (via ML) in near-real-time.
3. A working module capable of identifying suspicious patterns in encrypted traffic using
   metadata analysis.
4. An interactive web-based dashboard for visualizing network security alerts.
5. A comprehensive evaluation report benchmarking the system's performance and
   detection accuracy against public datasets.

## 8. Timeline

```
### Week 1-3
Phase Description Duration
Research & Design Environment setup, library selection, system
architecture design, dataset acquisition

### Week 4-8
Development Traffic capture, feature extraction, rule-based
detection (Tier 1), dashboard integration

### Week 9-11
Enhancement & Integration Grafana/InfluxDB setup, ML module (Tier 2, if
feasible), system integration

### Week 12-14
Testing & Documentation Dataset evaluation, performance benchmarking,
final report
```
