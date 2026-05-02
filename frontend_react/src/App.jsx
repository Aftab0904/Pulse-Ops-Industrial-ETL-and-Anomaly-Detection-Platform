import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ScatterChart, Scatter, Cell, AreaChart, Area
} from 'recharts';
import { 
  Activity, Database, Zap, RefreshCcw, AlertCircle, Server, Cpu, Layers, Box, CheckCircle
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const styles = {
  container: { display: 'flex', minHeight: '100vh', backgroundColor: '#f8fafc' },
  sidebar: {
    width: '320px',
    backgroundColor: '#1e293b',
    color: 'white',
    padding: '30px',
    display: 'flex',
    flexDirection: 'column',
    position: 'fixed',
    height: '100vh',
    boxShadow: '4px 0 15px rgba(0,0,0,0.1)',
    zIndex: 100
  },
  main: { flex: 1, marginLeft: '320px', padding: '50px' },
  header: { marginBottom: '40px' },
  card: {
    backgroundColor: 'white',
    borderRadius: '24px',
    padding: '30px',
    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
    border: '1px solid #e2e8f0',
    marginBottom: '30px'
  },
  btnPrimary: {
    backgroundColor: '#ff4b4b',
    color: 'white',
    border: 'none',
    padding: '15px',
    borderRadius: '12px',
    fontWeight: 'bold',
    cursor: 'pointer',
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
    boxShadow: '0 10px 15px -3px rgba(255, 75, 75, 0.2)'
  },
  btnSecondary: {
    backgroundColor: '#334155',
    color: 'white',
    border: 'none',
    padding: '15px',
    borderRadius: '12px',
    fontWeight: 'bold',
    cursor: 'pointer',
    width: '100%',
    marginTop: '10px'
  },
  metricCard: {
    backgroundColor: 'white',
    borderRadius: '20px',
    padding: '25px',
    border: '1px solid #e2e8f0',
    flex: 1
  },
  console: {
    backgroundColor: 'rgba(0,0,0,0.3)',
    borderRadius: '15px',
    padding: '15px',
    fontSize: '10px',
    fontFamily: 'monospace',
    height: '250px',
    overflowY: 'auto',
    color: '#10b981',
    marginTop: '20px',
    border: '1px solid rgba(255,255,255,0.1)'
  }
};

function App() {
  const [status, setStatus] = useState({ state: 'IDLE', logs: [] });
  const [features, setFeatures] = useState([]);
  const [anomalies, setAnomalies] = useState([]);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${API_BASE}/status`);
        setStatus(prev => {
          // If state transitions to FINISH, trigger a data fetch
          if (prev.state !== 'FINISH' && res.data.state === 'FINISH') {
            fetchData();
          }
          return res.data;
        });
      } catch (err) { console.error("Poll failed"); }
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [featRes, anonRes] = await Promise.all([
        axios.get(`${API_BASE}/analytics/features`),
        axios.get(`${API_BASE}/analytics/anomalies`)
      ]);
      setFeatures(Array.isArray(featRes.data) ? featRes.data : []);
      setAnomalies(Array.isArray(anonRes.data) ? anonRes.data : []);
    } catch (err) { console.error("Fetch failed"); }
  };

  useEffect(() => { fetchData(); }, []);

  const runPipeline = async () => {
    try {
      await axios.post(`${API_BASE}/ingest/nasa-auto`);
    } catch (err) { alert("Trigger failed"); }
  };

  return (
    <div style={styles.container}>
      {/* Sidebar */}
      <aside style={styles.sidebar}>
        <div style={{ marginBottom: '40px', borderBottom: '1px solid #334155', paddingBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
             <Activity color="#ff4b4b" size={32} />
             <h1 style={{ fontSize: '24px', fontWeight: '900', letterSpacing: '-1px' }}>PULSE<span style={{color:'#ff4b4b'}}>OPS</span></h1>
          </div>
          <p style={{ fontSize: '10px', color: '#64748b', fontWeight: 'bold', marginTop: '5px' }}>V2.5 INDUSTRIAL PLATFORM</p>
        </div>

        <div>
          <h3 style={{ fontSize: '11px', color: '#64748b', fontWeight: '900', marginBottom: '15px' }}>OPERATIONS</h3>
          <button onClick={runPipeline} style={styles.btnPrimary}><RefreshCcw size={18}/> RUN PIPELINE</button>
          <button onClick={fetchData} style={styles.btnSecondary}>REFRESH DATA</button>
        </div>

        <div style={{ marginTop: '40px', flex: 1, display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ fontSize: '11px', color: '#64748b', fontWeight: '900' }}>CLOUD LOGS</h3>
          <div style={styles.console} className="custom-scrollbar">
            {status.logs.map((log, i) => (
              <div key={i} style={{ marginBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '4px' }}>
                {log.split('] ').pop()}
              </div>
            ))}
            {status.logs.length === 0 && <div style={{ textAlign: 'center', opacity: 0.3, marginTop: '50px' }}>IDLE</div>}
          </div>
        </div>

        <div style={{ marginTop: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: status.state === 'FINISH' ? '#10b981' : '#f59e0b' }}></div>
          <span style={{ fontSize: '10px', fontWeight: 'bold' }}>SYSTEM: {status.state}</span>
        </div>
      </aside>

      {/* Main */}
      <main style={styles.main}>
        <div style={styles.header}>
          <h2 style={{ fontSize: '48px', fontWeight: '900', letterSpacing: '-2px', color: '#0f172a' }}>Pipeline <span style={{ color: '#94a3b8' }}>Monitor</span></h2>
          <p style={{ color: '#64748b', fontSize: '18px', fontWeight: '500' }}>End-to-End Industrial Data Lake Topology (S3 &rarr; Glue &rarr; Athena)</p>
        </div>

        {/* Metrics */}
        <div style={{ display: 'flex', gap: '25px', marginBottom: '40px' }}>
          <div style={styles.metricCard}>
            <div style={{ fontSize: '10px', fontWeight: '900', color: '#64748b', marginBottom: '10px' }}>S3 RECORD COUNT</div>
            <div style={{ fontSize: '36px', fontWeight: '900' }}>{features.length}</div>
          </div>
          <div style={styles.metricCard}>
            <div style={{ fontSize: '10px', fontWeight: '900', color: '#64748b', marginBottom: '10px' }}>AVG VIBRATION (RMS)</div>
            <div style={{ fontSize: '36px', fontWeight: '900' }}>{(features.reduce((a,b)=>a+(b.rms||0),0)/(features.length||1)).toFixed(4)}</div>
          </div>
          <div style={styles.metricCard}>
            <div style={{ fontSize: '10px', fontWeight: '900', color: '#64748b', marginBottom: '10px' }}>ANOMALIES DETECTED</div>
            <div style={{ fontSize: '36px', fontWeight: '900', color: '#ef4444' }}>{anomalies.filter(a=>a.is_anomaly===1).length}</div>
          </div>
        </div>

        {/* Pipeline Map */}
        <div style={styles.card}>
          <h3 style={{ marginBottom: '25px', fontWeight: '900', color: '#1e293b' }}>AWS INFRASTRUCTURE MAPPING</h3>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            {[
              { n: 'S3', l: 'Landing', i: Database },
              { n: 'Lambda', l: 'Ingest', i: Zap },
              { n: 'Glue', l: 'ETL Job', i: Cpu },
              { n: 'Athena', l: 'Analytics', i: Box }
            ].map((step, idx) => (
              <div key={idx} style={{ textAlign: 'center', flex: 1 }}>
                <div style={{ width: '60px', height: '60px', backgroundColor: '#f1f5f9', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyCenter: 'center', margin: '0 auto 15px', display: 'flex', justifyContent: 'center' }}>
                  <step.i size={24} color="#64748b" />
                </div>
                <div style={{ fontWeight: '900', fontSize: '14px' }}>{step.n}</div>
                <div style={{ fontSize: '10px', color: '#94a3b8', fontWeight: 'bold' }}>{step.l}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Charts */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '30px' }}>
          <div style={styles.card}>
            <h3 style={{ marginBottom: '20px', fontWeight: '900' }}>ETL SIGNAL TREND</h3>
            <div style={{ height: '350px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={features}>
                  <defs>
                    <linearGradient id="colorRms" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="file_path" hide={false} stroke="#1e293b" fontSize={10} tickLine={true} axisLine={true} />
                  <YAxis axisLine={true} tickLine={true} fontSize={10} stroke="#1e293b" />
                  <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0' }} />
                  <Area type="monotone" dataKey="rms" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorRms)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div style={styles.card}>
            <h3 style={{ marginBottom: '20px', fontWeight: '900' }}>ML CLUSTERS</h3>
            <div style={{ height: '350px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" dataKey="rms" name="RMS" stroke="#1e293b" fontSize={10} label={{ value: 'RMS', position: 'insideBottom', offset: -5 }} />
                  <YAxis type="number" dataKey="std" name="Std" stroke="#1e293b" fontSize={10} label={{ value: 'Std', position: 'insideLeft', angle: -90 }} />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                  <Scatter data={anomalies}>
                    {anomalies.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.is_anomaly === 1 ? '#ef4444' : '#3b82f6'} fillOpacity={0.6} />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
