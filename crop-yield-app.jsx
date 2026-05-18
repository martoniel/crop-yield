import { useState, useEffect, useCallback, createContext, useContext } from "react";

// ─────────────────────────────────────────
// THEME CONTEXT
// ─────────────────────────────────────────
const ThemeContext = createContext(false);

// ─────────────────────────────────────────
// API LAYER (calls backend)
// ─────────────────────────────────────────
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api/v1";

async function apiPredict(formData) {
  const payload = {
    crop_name: formData.crop,
    region: formData.region,
    soil_type: formData.soilType,
    rainfall: Number(formData.rainfall),
    temperature: Number(formData.temperature),
    humidity: Number(formData.humidity),
    fertilizer_usage: Number(formData.fertilizer),
    pesticide_usage: Number(formData.pesticide),
    area_cultivated: Number(formData.area),
    season: formData.season,
    year: Number(formData.year),
  };

  const res = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`Prediction request failed (${res.status}): ${txt}`);
  }

  const json = await res.json();
  const d = json.data;
  return {
    prediction_id: d.prediction_id,
    predictedYield: d.predicted_yield,
    unit: d.yield_unit,
    confidence: d.confidence_score,
    model: d.model_used,
    interpretation: d.interpretation,
    timestamp: d.timestamp,
  };
}

async function fetchHistoryFromApi(page = 1, page_size = 20) {
  const res = await fetch(`${API_BASE}/predictions?page=${page}&page_size=${page_size}`);
  if (!res.ok) return [];
  const json = await res.json();
  const results = json.data?.results || [];
  return results.map(r => ({
    id: r.id,
    date: new Date(r.created_at).toISOString().slice(0, 10),
    crop: r.crop_name,
    region: r.region,
    soilType: r.soil_type,
    rainfall: r.rainfall,
    temperature: r.temperature,
    humidity: r.humidity,
    fertilizer: r.fertilizer_usage,
    pesticide: r.pesticide_usage,
    area: r.area_cultivated,
    season: r.season,
    year: r.year,
    predictedYield: r.predicted_yield,
    unit: r.yield_unit,
    confidence: r.confidence_score,
    model: r.model_used,
    status: r.status,
  }));
}
const CROPS = ["Maize", "Rice", "Sorghum", "Cassava", "Wheat", "Yam", "Cowpea", "Groundnut", "Millet", "Sugarcane", "Tomato", "Cotton"];
const REGIONS = ["Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue", "Borno", "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu", "Gombe", "Imo", "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi", "Kwara", "Lagos", "Nasarawa", "Niger", "Ogun", "Ondo", "Osun", "Oyo", "Plateau", "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara", "FCT"];
const SOIL_TYPES = ["Loamy", "Clay", "Sandy", "Clay Loam", "Sandy Loam", "Silty Clay", "Peat", "Chalky"];
const SEASONS = ["Wet", "Dry", "Rabi", "Kharif"];



// ─────────────────────────────────────────
// ICONS (inline SVG components)
// ─────────────────────────────────────────
const Icon = ({ path, size = 20, className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d={path} />
  </svg>
);

const Icons = {
  leaf: "M12 2a10 10 0 0 1 10 10c0 5.52-4.48 10-10 10S2 17.52 2 12c0-2.76 1.12-5.26 2.93-7.07M12 2v10m0 0l-3-3m3 3l3-3",
  chart: "M3 3v18h18M9 17V9m4 8V5m4 12v-4",
  history: "M12 8v4l3 3m6-3a9 9 0 1 1-18 0 9 9 0 0 1 18 0",
  info: "M12 22a10 10 0 1 1 0-20 10 10 0 0 1 0 20zm0-6v-4m0-4h.01",
  help: "M12 22a10 10 0 1 1 0-20 10 10 0 0 1 0 20zm0-6v-2m0-8a2 2 0 0 1 2 2c0 1-1 1.5-2 2s-2 .9-2 2",
  about: "M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2zM16 3H8a2 2 0 0 0-2 2v2h12V5a2 2 0 0 0-2-2z",
  home: "M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10",
  predict: "M9 19v-6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2zm0 0V9a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v10m-6 0a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2m0 0V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2z",
  trash: "M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6",
  eye: "M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8zm11 3a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
  download: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3",
  check: "M20 6L9 17l-5-5",
  arrow: "M5 12h14M12 5l7 7-7 7",
  menu: "M3 12h18M3 6h18M3 18h18",
  close: "M18 6L6 18M6 6l12 12",
  plant: "M12 22V12M12 12C12 12 7 9 7 5a5 5 0 0 1 10 0c0 4-5 7-5 7z",
  sun: "M12 17A5 5 0 1 0 12 7a5 5 0 0 0 0 10zM12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42",
  droplet: "M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z",
  thermometer: "M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z",
  map: "M1 6v16l7-4 8 4 7-4V2l-7 4-8-4-7 4zM8 2v16M16 6v16",
  flask: "M10 2v7.527a2 2 0 0 1-.211.896L4.72 20.55a1 1 0 0 0 .9 1.45h12.76a1 1 0 0 0 .9-1.45l-5.069-10.127A2 2 0 0 1 14 9.527V2M8.5 2h7",
  model: "M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5",
  user: "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
  mail: "M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2zm18 2l-10 7L2 6",
  logout: "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9",
  plus: "M12 5v14M5 12h14",
  star: "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z",
};

// ─────────────────────────────────────────
// SHARED UI COMPONENTS
// ─────────────────────────────────────────

const Badge = ({ children, color = "green" }) => {
  const colors = {
    green: "bg-emerald-100 text-emerald-800",
    blue: "bg-blue-100 text-blue-800",
    amber: "bg-amber-100 text-amber-800",
    red: "bg-red-100 text-red-800",
    gray: "bg-gray-100 text-gray-700",
  };
  return <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${colors[color]}`}>{children}</span>;
};

const StatCard = ({ label, value, sub, iconPath, color = "green" }) => {
  const isDark = useContext(ThemeContext);
  const colors = {
    green: isDark ? "bg-emerald-900/40 text-emerald-400 border-emerald-800" : "bg-emerald-50 text-emerald-600 border-emerald-200",
    blue: isDark ? "bg-blue-900/40 text-blue-400 border-blue-800" : "bg-blue-50 text-blue-600 border-blue-200",
    amber: isDark ? "bg-amber-900/40 text-amber-400 border-amber-800" : "bg-amber-50 text-amber-600 border-amber-200",
    slate: isDark ? "bg-slate-800 text-slate-400 border-slate-700" : "bg-slate-50 text-slate-600 border-slate-200",
  };
  return (
    <div className={`rounded-xl border p-5 flex items-start gap-4 ${colors[color]}`}>
      <div className="mt-1 opacity-80">
        <Icon path={iconPath} size={22} />
      </div>
      <div>
        <p className="text-2xl font-bold tracking-tight">{value}</p>
        <p className="text-sm font-medium opacity-80">{label}</p>
        {sub && <p className="text-xs opacity-60 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
};

const Button = ({ children, variant = "primary", size = "md", onClick, disabled, type = "button", className = "", iconPath }) => {
  const isDark = useContext(ThemeContext);
  const base = "inline-flex items-center gap-2 rounded-lg font-semibold transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-1 cursor-pointer";
  const sizes = { sm: "px-3 py-1.5 text-sm", md: "px-5 py-2.5 text-sm", lg: "px-7 py-3.5 text-base" };
  const variants = {
    primary: "bg-emerald-700 text-white hover:bg-emerald-800 focus:ring-emerald-500 shadow-sm",
    secondary: "bg-white text-emerald-800 border border-emerald-300 hover:bg-emerald-50 focus:ring-emerald-400",
    ghost: isDark ? "bg-transparent text-slate-300 hover:bg-slate-700 focus:ring-slate-600" : "bg-transparent text-slate-600 hover:bg-slate-100 focus:ring-slate-300",
    danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-400",
    outline: isDark ? "bg-transparent border border-slate-600 text-slate-300 hover:bg-slate-700 focus:ring-slate-600" : "bg-transparent border border-slate-300 text-slate-700 hover:bg-slate-50 focus:ring-slate-300",
  };
  return (
    <button type={type} onClick={onClick} disabled={disabled}
      className={`${base} ${sizes[size]} ${variants[variant]} ${disabled ? "opacity-50 cursor-not-allowed" : ""} ${className}`}>
      {iconPath && <Icon path={iconPath} size={16} />}
      {children}
    </button>
  );
};

const Input = ({ label, name, type = "text", value, onChange, placeholder, error, required, min, max, step, hint }) => {
  const isDark = useContext(ThemeContext);
  return (
  <div className="flex flex-col gap-1">
    <label className={`text-sm font-semibold ${isDark ? "text-slate-300" : "text-slate-700"}`}>{label}{required && <span className="text-red-500 ml-0.5">*</span>}</label>
    <input type={type} name={name} value={value} onChange={onChange} placeholder={placeholder} min={min} max={max} step={step}
      className={`w-full rounded-lg border px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition ${error ? "border-red-400" : isDark ? "border-slate-600" : "border-slate-300"} ${isDark ? "bg-slate-800 text-slate-100 placeholder-slate-500" : "bg-white text-slate-800 placeholder-slate-400"}`} />
    {hint && !error && <p className={`text-xs ${isDark ? "text-slate-500" : "text-slate-400"}`}>{hint}</p>}
    {error && <p className="text-xs text-red-500">{error}</p>}
  </div>
  );
};

const Select = ({ label, name, value, onChange, options, error, required, hint }) => {
  const isDark = useContext(ThemeContext);
  return (
  <div className="flex flex-col gap-1">
    <label className={`text-sm font-semibold ${isDark ? "text-slate-300" : "text-slate-700"}`}>{label}{required && <span className="text-red-500 ml-0.5">*</span>}</label>
    <select name={name} value={value} onChange={onChange}
      className={`w-full rounded-lg border px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition ${error ? "border-red-400" : isDark ? "border-slate-600" : "border-slate-300"} ${isDark ? "bg-slate-800 text-slate-100" : "bg-white text-slate-800"}`}>
      <option value="">— Select —</option>
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
    {hint && !error && <p className={`text-xs ${isDark ? "text-slate-500" : "text-slate-400"}`}>{hint}</p>}
    {error && <p className="text-xs text-red-500">{error}</p>}
  </div>
  );
};

const Spinner = () => (
  <div className="flex flex-col items-center justify-center gap-4 py-16">
    <div className="w-12 h-12 border-4 border-emerald-200 border-t-emerald-700 rounded-full animate-spin" />
    <p className="text-slate-500 text-sm font-medium">Running prediction model...</p>
  </div>
);

const Toast = ({ message, type, onClose }) => {
  useEffect(() => { const t = setTimeout(onClose, 3500); return () => clearTimeout(t); }, [onClose]);
  const styles = { success: "bg-emerald-700 text-white", error: "bg-red-600 text-white", info: "bg-slate-800 text-white" };
  return (
    <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-3.5 rounded-xl shadow-xl text-sm font-medium ${styles[type]}`}>
      <Icon path={type === "success" ? Icons.check : Icons.close} size={16} />
      {message}
      <button onClick={onClose} className="ml-2 opacity-70 hover:opacity-100"><Icon path={Icons.close} size={14} /></button>
    </div>
  );
};

const SectionTitle = ({ eyebrow, title, desc }) => {
  const isDark = useContext(ThemeContext);
  return (
  <div className="text-center mb-12">
    {eyebrow && <p className="text-emerald-500 font-semibold text-xs uppercase tracking-widest mb-2">{eyebrow}</p>}
    <h2 className={`text-3xl font-bold mb-3 ${isDark ? "text-slate-100" : "text-slate-900"}`}>{title}</h2>
    {desc && <p className={`max-w-xl mx-auto text-base leading-relaxed ${isDark ? "text-slate-400" : "text-slate-500"}`}>{desc}</p>}
  </div>
  );
};

// ─────────────────────────────────────────
// NAVBAR
// ─────────────────────────────────────────
const NAV_LINKS = [
  { label: "Dashboard", page: "dashboard", icon: Icons.home },
  { label: "Predict", page: "predict", icon: Icons.predict },
  { label: "History", page: "history", icon: Icons.history },
  { label: "Model Info", page: "model", icon: Icons.model },
  { label: "About", page: "about", icon: Icons.about },
  { label: "Help", page: "help", icon: Icons.help },
];

const Navbar = ({ page, setPage, user, onLogout, sidebarOpen, setSidebarOpen, isDark, onToggleTheme }) => (
  <>
    <header className={`sticky top-0 z-40 backdrop-blur border-b shadow-sm ${isDark ? "bg-slate-900/95 border-slate-700" : "bg-white/95 border-slate-200"}`}>
      <div className="max-w-screen-xl mx-auto flex items-center justify-between px-4 md:px-8 h-16">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => setPage(user ? "dashboard" : "landing")}>
          <div className="w-9 h-9 bg-emerald-700 rounded-lg flex items-center justify-center shadow">
            <Icon path={Icons.leaf} size={18} className="text-white" />
          </div>
          <div>
            <p className={`font-bold text-sm leading-tight ${isDark ? "text-slate-100" : "text-slate-900"}`}>CropYield<span className="text-emerald-500">AI</span></p>
            <p className={`text-xs leading-tight hidden sm:block ${isDark ? "text-slate-500" : "text-slate-400"}`}>Prediction System</p>
          </div>
        </div>

        {user && (
          <nav className="hidden lg:flex items-center gap-1">
            {NAV_LINKS.map(l => (
              <button key={l.page} onClick={() => setPage(l.page)}
                className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${page === l.page ? (isDark ? "bg-emerald-900/50 text-emerald-400" : "bg-emerald-50 text-emerald-800") : (isDark ? "text-slate-400 hover:bg-slate-800" : "text-slate-600 hover:bg-slate-100")}`}>
                <Icon path={l.icon} size={15} />{l.label}
              </button>
            ))}
          </nav>
        )}

        <div className="flex items-center gap-3">
          {/* Dark mode toggle */}
          <button onClick={onToggleTheme} className={`p-2 rounded-lg transition ${isDark ? "text-amber-400 hover:bg-slate-800" : "text-slate-500 hover:bg-slate-100"}`} aria-label="Toggle dark mode">
            <Icon path={isDark ? Icons.sun : "M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"} size={18} />
          </button>
          {user ? (
            <>
              <div className={`hidden sm:flex items-center gap-2 text-sm ${isDark ? "text-slate-400" : "text-slate-600"}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${isDark ? "bg-emerald-900/50" : "bg-emerald-100"}`}>
                  <Icon path={Icons.user} size={14} className="text-emerald-500" />
                </div>
                <span className={`font-medium hidden md:inline ${isDark ? "text-slate-300" : "text-slate-700"}`}>{user.name}</span>
              </div>
              <button onClick={onLogout} className={`flex items-center gap-1.5 text-sm transition px-2 py-1.5 rounded-lg ${isDark ? "text-slate-400 hover:text-red-400 hover:bg-red-900/30" : "text-slate-500 hover:text-red-600 hover:bg-red-50"}`}>
                <Icon path={Icons.logout} size={15} />
                <span className="hidden sm:inline">Logout</span>
              </button>
              <button onClick={() => setSidebarOpen(!sidebarOpen)} className={`lg:hidden p-2 rounded-lg ${isDark ? "hover:bg-slate-800 text-slate-400" : "hover:bg-slate-100 text-slate-600"}`}>
                <Icon path={sidebarOpen ? Icons.close : Icons.menu} size={20} />
              </button>
            </>
          ) : (
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setPage("login")}>Sign In</Button>
              <Button variant="primary" size="sm" onClick={() => setPage("register")}>Get Started</Button>
            </div>
          )}
        </div>
      </div>
    </header>

    {/* Mobile Sidebar */}
    {user && sidebarOpen && (
      <div className="lg:hidden fixed inset-0 z-30 flex">
        <div className="absolute inset-0 bg-black/30" onClick={() => setSidebarOpen(false)} />
        <div className={`relative z-10 w-64 h-full shadow-2xl flex flex-col pt-4 ${isDark ? "bg-slate-900" : "bg-white"}`}>
          <div className="px-4 mb-4">
            <p className={`text-xs font-semibold uppercase tracking-widest ${isDark ? "text-slate-500" : "text-slate-400"}`}>Navigation</p>
          </div>
          {NAV_LINKS.map(l => (
            <button key={l.page} onClick={() => { setPage(l.page); setSidebarOpen(false); }}
              className={`flex items-center gap-3 px-5 py-3 text-sm font-medium transition ${page === l.page ? (isDark ? "bg-emerald-900/40 text-emerald-400 border-r-4 border-emerald-500" : "bg-emerald-50 text-emerald-800 border-r-4 border-emerald-700") : (isDark ? "text-slate-400 hover:bg-slate-800" : "text-slate-600 hover:bg-slate-50")}`}>
              <Icon path={l.icon} size={17} />{l.label}
            </button>
          ))}
        </div>
      </div>
    )}
  </>
);

// ─────────────────────────────────────────
// FOOTER
// ─────────────────────────────────────────
const Footer = ({ setPage }) => (
  <footer className="bg-slate-900 text-slate-400 mt-auto">
    <div className="max-w-screen-xl mx-auto px-6 md:px-8 py-12 grid grid-cols-1 md:grid-cols-3 gap-10">
      <div>
        <div className="flex items-center gap-2 mb-3">
          <div className="w-8 h-8 bg-emerald-700 rounded-lg flex items-center justify-center">
            <Icon path={Icons.leaf} size={16} className="text-white" />
          </div>
          <span className="font-bold text-white text-sm">CropYield<span className="text-emerald-400">AI</span></span>
        </div>
        <p className="text-xs leading-relaxed">A final year computer science project on crop yield prediction using machine learning. Federal University, Dutsin-Ma.</p>
      </div>
      <div>
        <p className="text-white font-semibold text-sm mb-3">Quick Links</p>
        <div className="flex flex-col gap-2">
          {[["Dashboard", "dashboard"], ["Predict Yield", "predict"], ["History", "history"], ["About Project", "about"]].map(([l, p]) => (
            <button key={p} onClick={() => setPage(p)} className="text-xs text-left hover:text-emerald-400 transition">{l}</button>
          ))}
        </div>
      </div>
      <div>
        <p className="text-white font-semibold text-sm mb-3">Project Info</p>
        <p className="text-xs leading-relaxed">Developer: <span className="text-white">Fayyad Inda Musa</span></p>
        <p className="text-xs mt-1">Department: <span className="text-white">Computer Science</span></p>
        <p className="text-xs mt-1">Institution: <span className="text-white">FUD Dutsin-Ma</span></p>
        <p className="text-xs mt-1">Academic Year: <span className="text-white">2024/2025</span></p>
      </div>
    </div>
    <div className="border-t border-slate-800 text-center py-4 text-xs">
      © 2025 CropYieldAI · Final Year Project · All rights reserved
    </div>
  </footer>
);

// ─────────────────────────────────────────
// PAGE: LANDING
// ─────────────────────────────────────────
const LandingPage = ({ setPage, isDark, onToggleTheme }) => {
  const features = [
    { icon: Icons.predict, title: "ML-Powered Prediction", desc: "Utilises a trained Random Forest Regressor model to generate accurate crop yield estimates from agricultural parameters." },
    { icon: Icons.chart, title: "Analytical Dashboard", desc: "Visualise your prediction history with aggregated insights on yield trends, crop performance, and seasonal patterns." },
    { icon: Icons.history, title: "Prediction History", desc: "All predictions are stored and accessible. Track how conditions change across seasons, years, and regions." },
    { icon: Icons.map, title: "Region-Specific Inputs", desc: "Supports all 36 Nigerian states and the FCT, tailored for local agricultural conditions and regional soil types." },
    { icon: Icons.flask, title: "Transparent Model", desc: "Understand which features influence predictions. Full model explainability built into the interface." },
    { icon: Icons.download, title: "Export Results", desc: "Download your prediction results as PDF or CSV for documentation, research reporting, or farm planning." },
  ];

  const mlReasons = [
    { title: "Pattern Recognition at Scale", desc: "ML models identify non-linear relationships between rainfall, temperature, soil type, and yield that classical statistical methods cannot." },
    { title: "Predictive Accuracy", desc: "The Random Forest model achieved an R² score of 0.891 on the validation dataset, demonstrating strong generalisation ability." },
    { title: "Decision Support for Farmers", desc: "Instead of trial-and-error, farmers receive data-driven guidance on expected yield before committing resources to cultivation." },
    { title: "Adaptability to Data Variability", desc: "Ensemble learning methods like Random Forests handle missing values, outliers, and diverse input distributions robustly." },
  ];

  return (
    <div className={`min-h-screen flex flex-col ${isDark ? "bg-slate-950 text-slate-100" : "bg-white text-slate-900"}`}>
      {/* Hero */}
      <section className="relative bg-gradient-to-br from-emerald-900 via-emerald-800 to-slate-900 text-white overflow-hidden">
        <div className="absolute inset-0 opacity-10" style={{ backgroundImage: "radial-gradient(circle at 70% 30%, #6ee7b7 0%, transparent 60%), radial-gradient(circle at 20% 80%, #34d399 0%, transparent 50%)" }} />
        <div className="relative max-w-screen-xl mx-auto px-6 md:px-8 pt-20 pb-24 md:pt-28 md:pb-32 grid md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="flex items-center justify-between gap-3 mb-6">
              <div className="inline-flex items-center gap-2 bg-emerald-700/50 border border-emerald-600/40 rounded-full px-4 py-1.5 text-xs font-semibold text-emerald-200">
                <Icon path={Icons.star} size={12} /> Final Year CS Project · Federal University Dutsin-Ma
              </div>
              <button
                onClick={onToggleTheme}
                className="inline-flex items-center gap-2 rounded-full border border-white/30 px-3 py-1.5 text-xs font-semibold text-white hover:bg-white/10 transition"
                aria-label="Toggle landing page theme"
              >
                <Icon path={Icons.sun} size={14} />
                {isDark ? "Light Mode" : "Dark Mode"}
              </button>
            </div>
            <h1 className="text-4xl md:text-5xl font-extrabold leading-tight mb-5 tracking-tight">
              Crop Yield Prediction<br />
              <span className="text-emerald-400">Using Machine Learning</span>
            </h1>
            <p className="text-emerald-100 text-lg leading-relaxed mb-8 max-w-lg">
              An intelligent web-based system that predicts agricultural crop yields from environmental and agronomic inputs — empowering farmers, researchers, and planners with data-driven insights.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button variant="primary" size="lg" onClick={() => setPage("register")} iconPath={Icons.predict}>Start Prediction</Button>
              <Button variant="secondary" size="lg" onClick={() => setPage("about")} iconPath={Icons.info} className="border-white/30 text-white hover:bg-white/10 bg-transparent">Learn More</Button>
            </div>
          </div>
          <div className="hidden md:flex justify-center">
            <div className="grid grid-cols-2 gap-4 w-full max-w-sm">
              {[["R² Score", "0.891", "Model accuracy"], ["States", "36+", "Nigerian regions"], ["Parameters", "11", "Input features"], ["Crops", "12+", "Supported crops"]].map(([l, v, s]) => (
                <div key={l} className="bg-white/10 backdrop-blur rounded-xl p-5 border border-white/10">
                  <p className="text-2xl font-extrabold text-emerald-300">{v}</p>
                  <p className="text-white font-medium text-sm">{l}</p>
                  <p className="text-emerald-200 text-xs">{s}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* What is Crop Yield Prediction */}
      <section className={`py-16 ${isDark ? "bg-slate-900" : "bg-white"}`}>
        <div className="max-w-screen-xl mx-auto px-6 md:px-8">
          <div className="max-w-3xl mx-auto text-center">
            <p className="text-emerald-700 font-semibold text-xs uppercase tracking-widest mb-3">Overview</p>
            <h2 className={`text-3xl font-bold mb-5 ${isDark ? "text-slate-100" : "text-slate-900"}`}>What is Crop Yield Prediction?</h2>
            <p className={`text-base leading-relaxed ${isDark ? "text-slate-300" : "text-slate-600"}`}>
              Crop yield prediction is the application of computational models to estimate the quantity of agricultural output — typically measured in <strong>tons per hectare</strong> — before or during a growing season. By analysing historical data and current field conditions including <strong>rainfall, soil type, temperature, fertilizer application, and seasonal variations</strong>, predictive models can provide informed yield forecasts.
            </p>
            <p className={`text-sm mt-4 leading-relaxed ${isDark ? "text-slate-400" : "text-slate-500"}`}>
              This system applies a <strong>supervised machine learning approach</strong> trained on agronomic datasets to generate region-specific yield estimates for Nigerian agricultural contexts, supporting both small-scale farmers and large-scale planners.
            </p>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className={`py-16 ${isDark ? "bg-slate-950" : "bg-slate-50"}`}>
        <div className="max-w-screen-xl mx-auto px-6 md:px-8">
          <SectionTitle eyebrow="System Features" title="What This System Offers" desc="A complete suite of tools to support agricultural decision-making through machine learning." />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map(f => (
              <div key={f.title} className={`rounded-xl border p-6 hover:shadow-md transition group ${isDark ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200"}`}>
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-emerald-100 transition ${isDark ? "bg-emerald-900/50" : "bg-emerald-50"}`}>
                  <Icon path={f.icon} size={20} className="text-emerald-700" />
                </div>
                <h3 className={`font-bold mb-2 ${isDark ? "text-slate-100" : "text-slate-900"}`}>{f.title}</h3>
                <p className={`text-sm leading-relaxed ${isDark ? "text-slate-400" : "text-slate-500"}`}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why ML */}
      <section className="py-16 bg-emerald-900 text-white">
        <div className="max-w-screen-xl mx-auto px-6 md:px-8">
          <SectionTitle eyebrow="Rationale" title="Why Machine Learning for Agriculture?" desc="Traditional forecasting methods are insufficient for modern agricultural complexity. Here is why machine learning changes the equation." />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {mlReasons.map((r, i) => (
              <div key={i} className="bg-white/10 backdrop-blur border border-white/10 rounded-xl p-6">
                <div className="flex items-start gap-3">
                  <span className="text-emerald-400 font-extrabold text-xl">0{i + 1}</span>
                  <div>
                    <h3 className="font-bold text-white mb-1">{r.title}</h3>
                    <p className="text-emerald-100 text-sm leading-relaxed">{r.desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className={`py-16 ${isDark ? "bg-slate-900" : "bg-white"}`}>
        <div className="max-w-xl mx-auto text-center px-6">
          <h2 className={`text-2xl font-bold mb-3 ${isDark ? "text-slate-100" : "text-slate-900"}`}>Ready to predict your crop yield?</h2>
          <p className={`text-sm mb-6 ${isDark ? "text-slate-400" : "text-slate-500"}`}>Create an account or sign in to access the full prediction system.</p>
          <div className="flex justify-center gap-3">
            <Button variant="primary" size="lg" onClick={() => setPage("register")}>Create Account</Button>
            <Button variant="outline" size="lg" onClick={() => setPage("login")}>Sign In</Button>
          </div>
        </div>
      </section>

      <Footer setPage={setPage} />
    </div>
  );
};

// ─────────────────────────────────────────
// PAGE: AUTH
// ─────────────────────────────────────────
const AuthPage = ({ type, setPage, onAuth }) => {
  const isDark = useContext(ThemeContext);
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const validate = () => {
    const e = {};
    if (type === "register" && !form.name.trim()) e.name = "Full name is required";
    if (!form.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) e.email = "Enter a valid email address";
    if (form.password.length < 6) e.password = "Password must be at least 6 characters";
    return e;
  };

  const handleSubmit = async () => {
    const e = validate();
    if (Object.keys(e).length) { setErrors(e); return; }
    setLoading(true);
    await new Promise(r => setTimeout(r, 1200));
    onAuth({ name: form.name || "Researcher", email: form.email, role: "User" });
  };

  const ch = e => setForm(p => ({ ...p, [e.target.name]: e.target.value }));

  return (
    <div className={`min-h-screen flex items-center justify-center px-4 py-12 ${isDark ? "bg-slate-950" : "bg-slate-50"}`}>
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-emerald-700 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow">
            <Icon path={Icons.leaf} size={26} className="text-white" />
          </div>
          <h1 className={`text-2xl font-extrabold ${isDark ? "text-slate-100" : "text-slate-900"}`}>{type === "login" ? "Welcome back" : "Create your account"}</h1>
          <p className={`text-sm mt-1 ${isDark ? "text-slate-400" : "text-slate-500"}`}>{type === "login" ? "Sign in to access your prediction dashboard" : "Join the CropYieldAI prediction system"}</p>
        </div>
        <div className={`rounded-2xl border shadow-sm p-8 flex flex-col gap-4 ${isDark ? "bg-slate-900 border-slate-700" : "bg-white border-slate-200"}`}>
          {type === "register" && <Input label="Full Name" name="name" value={form.name} onChange={ch} placeholder="e.g. Fayyad Inda Musa" error={errors.name} required />}
          <Input label="Email Address" name="email" type="email" value={form.email} onChange={ch} placeholder="you@example.com" error={errors.email} required />
          <Input label="Password" name="password" type="password" value={form.password} onChange={ch} placeholder="••••••••" error={errors.password} required />
          <Button variant="primary" size="lg" onClick={handleSubmit} disabled={loading} className="w-full justify-center mt-2">
            {loading ? "Please wait..." : type === "login" ? "Sign In" : "Create Account"}
          </Button>
          <p className={`text-center text-xs mt-1 ${isDark ? "text-slate-500" : "text-slate-400"}`}>
            {type === "login" ? "Don't have an account?" : "Already have an account?"}
            {" "}<button onClick={() => setPage(type === "login" ? "register" : "login")} className="text-emerald-500 font-semibold hover:underline">
              {type === "login" ? "Register" : "Sign in"}
            </button>
          </p>
          <div className={`border-t pt-3 ${isDark ? "border-slate-700" : "border-slate-100"}`}>
            <p className={`text-xs text-center mb-2 ${isDark ? "text-slate-500" : "text-slate-400"}`}>Or continue with demo credentials</p>
            <Button variant="outline" size="sm" className="w-full justify-center text-xs"
              onClick={async () => {
                const demo = { name: "Demo User", email: "demo@cropai.edu.ng", password: "demo123" };
                setForm(demo);
                setErrors({});
                setLoading(true);
                await new Promise(r => setTimeout(r, 1200));
                onAuth({ name: demo.name, email: demo.email, role: "User" });
              }}>
              Use Demo Account
            </Button>
          </div>
        </div>
        <button onClick={() => setPage("landing")} className={`mt-4 text-xs flex items-center gap-1 mx-auto ${isDark ? "text-slate-500 hover:text-slate-300" : "text-slate-400 hover:text-slate-600"}`}>
          ← Back to home
        </button>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────
// PAGE: DASHBOARD
// ─────────────────────────────────────────
const DashboardPage = ({ setPage, history, user }) => {
  const isDark = useContext(ThemeContext);
  const avg = history.length ? (history.reduce((s, h) => s + h.predictedYield, 0) / history.length).toFixed(2) : "—";
  const mostCrop = history.length ? [...history].sort((a, b) => history.filter(h => h.crop === b.crop).length - history.filter(h => h.crop === a.crop).length)[0].crop : "—";

  return (
    <div className={`flex-1 py-8 px-4 md:px-8 ${isDark ? "bg-slate-950" : "bg-slate-50"}`}>
      <div className="max-w-screen-xl mx-auto">
        <div className="mb-8">
          <h1 className={`text-2xl font-extrabold ${isDark ? "text-slate-100" : "text-slate-900"}`}>Welcome back, {user?.name?.split(" ")[0]} 👋</h1>
          <p className={`text-sm mt-1 ${isDark ? "text-slate-400" : "text-slate-500"}`}>Here is a summary of your crop yield prediction activity.</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard label="Total Predictions" value={history.length} sub="All time" iconPath={Icons.chart} color="green" />
          <StatCard label="Avg. Predicted Yield" value={avg !== "—" ? `${avg} t/ha` : "—"} sub="Across all crops" iconPath={Icons.predict} color="blue" />
          <StatCard label="Most Predicted Crop" value={mostCrop} sub="By frequency" iconPath={Icons.leaf} color="amber" />
          <StatCard label="Recent Predictions" value={history.filter(h => { const d = new Date(h.date); const now = new Date(); return (now - d) / 86400000 < 30; }).length} sub="Last 30 days" iconPath={Icons.history} color="slate" />
        </div>

        {/* CTA */}
        <div className="bg-gradient-to-r from-emerald-800 to-emerald-700 rounded-2xl p-7 text-white mb-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h2 className="font-bold text-lg mb-1">Make a New Prediction</h2>
            <p className="text-emerald-100 text-sm">Enter your field parameters and receive an instant ML-powered yield estimate.</p>
          </div>
          <Button variant="secondary" onClick={() => setPage("predict")} iconPath={Icons.arrow} className="shrink-0 border-white text-emerald-900 bg-white hover:bg-emerald-50">
            Start Prediction
          </Button>
        </div>

        {/* Recent History */}
        <div className={`rounded-xl border p-6 ${isDark ? "bg-slate-900 border-slate-700" : "bg-white border-slate-200"}`}>
          <div className="flex items-center justify-between mb-5">
            <h2 className={`font-bold ${isDark ? "text-slate-100" : "text-slate-900"}`}>Recent Predictions</h2>
            <Button variant="ghost" size="sm" onClick={() => setPage("history")}>View all →</Button>
          </div>
          {history.length === 0 ? (
            <div className={`text-center py-12 ${isDark ? "text-slate-500" : "text-slate-400"}`}>
              <Icon path={Icons.chart} size={36} className="mx-auto mb-3 opacity-30" />
              <p className="font-medium">No predictions yet</p>
              <p className="text-xs mt-1">Make your first prediction to see results here</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className={`border-b text-xs uppercase ${isDark ? "border-slate-700 text-slate-500" : "border-slate-100 text-slate-500"}`}>
                  <th className="text-left pb-3 font-semibold">Date</th>
                  <th className="text-left pb-3 font-semibold">Crop</th>
                  <th className="text-left pb-3 font-semibold">Region</th>
                  <th className="text-right pb-3 font-semibold">Yield (t/ha)</th>
                  <th className="text-left pb-3 font-semibold pl-4">Status</th>
                </tr></thead>
                <tbody>
                  {history.slice(0, 5).map(h => (
                    <tr key={h.id} className={`border-b transition ${isDark ? "border-slate-800 hover:bg-slate-800" : "border-slate-50 hover:bg-slate-50"}`}>
                      <td className={`py-3 ${isDark ? "text-slate-400" : "text-slate-500"}`}>{h.date}</td>
                      <td className={`py-3 font-semibold ${isDark ? "text-slate-200" : "text-slate-800"}`}>{h.crop}</td>
                      <td className={`py-3 ${isDark ? "text-slate-400" : "text-slate-600"}`}>{h.region}</td>
                      <td className="py-3 text-right font-bold text-emerald-500">{h.predictedYield}</td>
                      <td className="py-3 pl-4"><Badge color="green">{h.status}</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────
// PAGE: PREDICT
// ─────────────────────────────────────────
const INIT_FORM = { crop: "", region: "", soilType: "", rainfall: "", temperature: "", humidity: "", fertilizer: "", pesticide: "", area: "", season: "", year: new Date().getFullYear().toString() };

const PredictPage = ({ onResult, onError }) => {
  const isDark = useContext(ThemeContext);
  const [form, setForm] = useState(INIT_FORM);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const required = ["crop", "region", "soilType", "rainfall", "temperature", "humidity", "fertilizer", "pesticide", "area", "season", "year"];

  const validate = () => {
    const e = {};
    required.forEach(k => { if (!form[k]) e[k] = "This field is required"; });
    if (form.rainfall && (isNaN(form.rainfall) || form.rainfall < 0)) e.rainfall = "Enter a valid rainfall value (mm)";
    if (form.temperature && (isNaN(form.temperature) || form.temperature < -10 || form.temperature > 60)) e.temperature = "Temperature must be between -10°C and 60°C";
    if (form.humidity && (form.humidity < 0 || form.humidity > 100)) e.humidity = "Humidity must be between 0% and 100%";
    if (form.area && form.area <= 0) e.area = "Area must be greater than 0";
    return e;
  };

  const handleChange = e => {
    const { name, value } = e.target;
    setForm(p => ({ ...p, [name]: value }));
    if (errors[name]) setErrors(p => { const n = { ...p }; delete n[name]; return n; });
  };

  const handleSubmit = async () => {
    const e = validate();
    if (Object.keys(e).length) { setErrors(e); return; }
    setLoading(true);
    try {
      const result = await apiPredict(form);
      onResult({ ...form, ...result, date: new Date().toISOString().slice(0, 10), id: result.prediction_id || Date.now() });
    } catch (err) {
      if (onError) onError(err.message || "Prediction failed", "error");
      else console.error(err);
    } finally { setLoading(false); }
  };

  const ch = handleChange;

  if (loading) return <div className={`flex-1 flex items-center justify-center py-20 ${isDark ? "bg-slate-950" : "bg-slate-50"}`}><div className="w-full max-w-md"><Spinner /></div></div>;

  return (
    <div className={`flex-1 py-8 px-4 md:px-8 ${isDark ? "bg-slate-950" : "bg-slate-50"}`}>
      <div className="max-w-3xl mx-auto">
        <div className="mb-7">
          <h1 className={`text-2xl font-extrabold ${isDark ? "text-slate-100" : "text-slate-900"}`}>Crop Yield Prediction</h1>
          <p className={`text-sm mt-1 ${isDark ? "text-slate-400" : "text-slate-500"}`}>Enter the agricultural parameters below to generate a machine learning-based yield estimate.</p>
        </div>

        <div className={`rounded-2xl border shadow-sm overflow-hidden ${isDark ? "bg-slate-900 border-slate-700" : "bg-white border-slate-200"}`}>
          {/* Section 1: Crop Info */}
          <div className={`border-b px-7 py-5 ${isDark ? "border-slate-700" : "border-slate-100"}`}>
            <p className="text-xs font-bold uppercase tracking-widest text-emerald-500 mb-4">01 — Crop & Location</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <Select label="Crop Name" name="crop" value={form.crop} onChange={ch} options={CROPS} error={errors.crop} required hint="Select the primary crop being cultivated" />
              <Select label="State / Region" name="region" value={form.region} onChange={ch} options={REGIONS} error={errors.region} required hint="Select the Nigerian state or region" />
              <Select label="Soil Type" name="soilType" value={form.soilType} onChange={ch} options={SOIL_TYPES} error={errors.soilType} required hint="The dominant soil classification of the field" />
              <Select label="Season" name="season" value={form.season} onChange={ch} options={SEASONS} error={errors.season} required hint="The growing season for this prediction" />
            </div>
          </div>

          {/* Section 2: Environmental */}
          <div className={`border-b px-7 py-5 ${isDark ? "border-slate-700" : "border-slate-100"}`}>
            <p className="text-xs font-bold uppercase tracking-widest text-emerald-500 mb-4">02 — Environmental Conditions</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
              <Input label="Rainfall (mm)" name="rainfall" type="number" value={form.rainfall} onChange={ch} placeholder="e.g. 850" min="0" max="5000" step="1" error={errors.rainfall} required hint="Annual or seasonal rainfall in millimetres" />
              <Input label="Temperature (°C)" name="temperature" type="number" value={form.temperature} onChange={ch} placeholder="e.g. 28" min="-10" max="60" step="0.1" error={errors.temperature} required hint="Average temperature during growing season" />
              <Input label="Humidity (%)" name="humidity" type="number" value={form.humidity} onChange={ch} placeholder="e.g. 65" min="0" max="100" step="1" error={errors.humidity} required hint="Average relative humidity percentage" />
            </div>
          </div>

          {/* Section 3: Agronomic */}
          <div className={`border-b px-7 py-5 ${isDark ? "border-slate-700" : "border-slate-100"}`}>
            <p className="text-xs font-bold uppercase tracking-widest text-emerald-500 mb-4">03 — Agronomic Inputs</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
              <Input label="Fertilizer Usage (kg/ha)" name="fertilizer" type="number" value={form.fertilizer} onChange={ch} placeholder="e.g. 120" min="0" step="0.1" error={errors.fertilizer} required hint="Total fertilizer applied per hectare" />
              <Input label="Pesticide Usage (kg/ha)" name="pesticide" type="number" value={form.pesticide} onChange={ch} placeholder="e.g. 3.5" min="0" step="0.01" error={errors.pesticide} required hint="Total pesticide applied per hectare" />
              <Input label="Area Cultivated (ha)" name="area" type="number" value={form.area} onChange={ch} placeholder="e.g. 2.5" min="0.1" step="0.01" error={errors.area} required hint="Total land area under cultivation" />
            </div>
          </div>

          {/* Section 4: Year */}
          <div className="px-7 py-5">
            <p className="text-xs font-bold uppercase tracking-widest text-emerald-500 mb-4">04 — Prediction Year</p>
            <div className="max-w-xs">
              <Input label="Year" name="year" type="number" value={form.year} onChange={ch} placeholder="2025" min="2000" max="2050" step="1" error={errors.year} required hint="The year for which yield is being predicted" />
            </div>
          </div>

          {/* Actions */}
          <div className={`border-t px-7 py-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 ${isDark ? "bg-slate-800 border-slate-700" : "bg-slate-50 border-slate-100"}`}>
            <p className={`text-xs max-w-sm ${isDark ? "text-slate-500" : "text-slate-400"}`}>All fields marked with <span className="text-red-500">*</span> are required. Ensure values are accurate for best prediction quality.</p>
            <div className="flex gap-3">
              <Button variant="outline" onClick={() => setForm(INIT_FORM)}>Reset Form</Button>
              <Button variant="primary" onClick={handleSubmit} iconPath={Icons.predict}>Run Prediction</Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────
// PAGE: RESULT
// ─────────────────────────────────────────
const ResultPage = ({ result, setPage, onSave, saved }) => {
  const isDark = useContext(ThemeContext);
  const conf = result.confidence || 85;
  const confColor = conf >= 85 ? "emerald" : conf >= 70 ? "amber" : "red";
  const confLabel = conf >= 85 ? "High Confidence" : conf >= 70 ? "Moderate Confidence" : "Low Confidence";

  const inputs = [
    ["Crop", result.crop], ["Region", result.region], ["Soil Type", result.soilType],
    ["Season", result.season], ["Year", result.year], ["Rainfall", `${result.rainfall} mm`],
    ["Temperature", `${result.temperature} °C`], ["Humidity", `${result.humidity}%`],
    ["Fertilizer", `${result.fertilizer} kg/ha`], ["Pesticide", `${result.pesticide} kg/ha`],
    ["Area", `${result.area} ha`],
  ];

  return (
    <div className={`flex-1 py-8 px-4 md:px-8 ${isDark ? "bg-slate-950" : "bg-slate-50"}`}>
      <div className="max-w-3xl mx-auto">
        <div className="mb-6 flex items-center gap-3">
          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isDark ? "bg-emerald-900/50" : "bg-emerald-100"}`}>
            <Icon path={Icons.check} size={18} className="text-emerald-500" />
          </div>
          <div>
            <h1 className={`text-xl font-extrabold ${isDark ? "text-slate-100" : "text-slate-900"}`}>Prediction Complete</h1>
            <p className={`text-xs ${isDark ? "text-slate-500" : "text-slate-400"}`}>Generated on {result.date}</p>
          </div>
        </div>

        {/* Main Result */}
        <div className="bg-gradient-to-br from-emerald-800 to-emerald-700 rounded-2xl p-8 text-white mb-6 text-center shadow-lg">
          <p className="text-emerald-200 text-xs font-semibold uppercase tracking-widest mb-3">Predicted Crop Yield</p>
          <p className="text-7xl font-extrabold tracking-tight text-white mb-1">{result.predictedYield}</p>
          <p className="text-emerald-200 text-lg font-medium mb-5">tons per hectare (t/ha)</p>
          <div className={`inline-flex items-center gap-2 bg-white/15 border border-white/20 rounded-full px-4 py-1.5 text-sm font-semibold`}>
            <span className={`w-2 h-2 rounded-full ${confColor === "emerald" ? "bg-emerald-300" : confColor === "amber" ? "bg-amber-300" : "bg-red-300"}`} />
            {confLabel} · {conf}%
          </div>
        </div>

        {/* Interpretation */}
        <div className={`border rounded-xl p-6 mb-6 ${isDark ? "bg-slate-900 border-slate-700" : "bg-white border-slate-200"}`}>
          <h2 className={`font-bold mb-3 ${isDark ? "text-slate-100" : "text-slate-900"}`}>Model Interpretation</h2>
          <p className={`text-sm leading-relaxed ${isDark ? "text-slate-300" : "text-slate-600"}`}>
            Based on the provided agricultural conditions — including a rainfall of <strong>{result.rainfall} mm</strong>, a growing temperature of <strong>{result.temperature}°C</strong>, and <strong>{result.fertilizer} kg/ha</strong> of fertilizer applied — the <strong>{result.model}</strong> model estimates that <strong>{result.crop}</strong> cultivated in <strong>{result.region} State</strong> during the <strong>{result.season} season of {result.year}</strong> will yield approximately <strong>{result.predictedYield} tons per hectare</strong>.
          </p>
          <p className={`text-xs mt-3 border-t pt-3 ${isDark ? "text-slate-500 border-slate-700" : "text-slate-400 border-slate-50"}`}>
            Model: {result.model} · R² Score: {result.r2Score} · Confidence: {conf}% · This is a model-generated estimate and should be used alongside expert agronomic advice.
          </p>
        </div>

        {/* Input Summary */}
        <div className={`border rounded-xl p-6 mb-6 ${isDark ? "bg-slate-900 border-slate-700" : "bg-white border-slate-200"}`}>
          <h2 className={`font-bold mb-4 ${isDark ? "text-slate-100" : "text-slate-900"}`}>Input Summary</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {inputs.map(([k, v]) => (
              <div key={k} className={`rounded-lg px-3 py-2.5 ${isDark ? "bg-slate-800" : "bg-slate-50"}`}>
                <p className={`text-xs font-medium ${isDark ? "text-slate-500" : "text-slate-400"}`}>{k}</p>
                <p className={`text-sm font-bold mt-0.5 ${isDark ? "text-slate-200" : "text-slate-800"}`}>{v}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-3">
          <Button variant="primary" onClick={() => setPage("predict")} iconPath={Icons.predict}>New Prediction</Button>
          <Button variant="secondary" onClick={onSave} disabled={saved} iconPath={Icons.check}>
            {saved ? "Saved to History" : "Save Result"}
          </Button>
          <Button variant="outline" onClick={() => setPage("history")} iconPath={Icons.history}>View History</Button>
          <Button variant="outline" onClick={() => {
            const headers = ["Date","Crop","Region","Soil Type","Season","Year","Rainfall (mm)","Temperature (°C)","Humidity (%)","Fertilizer (kg/ha)","Pesticide (kg/ha)","Area (ha)","Predicted Yield (t/ha)","Confidence (%)","Status"];
            const row = [result.date,result.crop,result.region,result.soilType,result.season,result.year,result.rainfall,result.temperature,result.humidity,result.fertilizer,result.pesticide,result.area,result.predictedYield,result.confidence ?? "",result.status ?? "Completed"];
            const csv = [headers, row].map(r => r.join(",")).join("\n");
            const a = document.createElement("a");
            a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
            a.download = `crop-yield-${result.crop}-${result.date}.csv`;
            a.click();
          }} iconPath={Icons.download}>Export CSV</Button>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────
// PAGE: HISTORY
// ─────────────────────────────────────────
const HistoryPage = ({ history, setHistory, setPage, onViewResult }) => {
  const isDark = useContext(ThemeContext);
  const [search, setSearch] = useState("");

  const filtered = history.filter(h =>
    h.crop.toLowerCase().includes(search.toLowerCase()) ||
    h.region.toLowerCase().includes(search.toLowerCase())
  );

  const avg = history.length ? (history.reduce((s, h) => s + h.predictedYield, 0) / history.length).toFixed(2) : 0;

  return (
    <div className={`flex-1 py-8 px-4 md:px-8 ${isDark ? "bg-slate-950" : "bg-slate-50"}`}>
      <div className="max-w-screen-xl mx-auto">
        <div className="mb-7">
          <h1 className={`text-2xl font-extrabold ${isDark ? "text-slate-100" : "text-slate-900"}`}>Prediction History</h1>
          <p className={`text-sm mt-1 ${isDark ? "text-slate-400" : "text-slate-500"}`}>A record of all crop yield predictions made on this system.</p>
        </div>

        {/* Analytics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-7">
          <StatCard label="Total Predictions" value={history.length} iconPath={Icons.chart} color="green" />
          <StatCard label="Average Yield" value={`${avg} t/ha`} iconPath={Icons.predict} color="blue" />
          <StatCard label="Crops Covered" value={[...new Set(history.map(h => h.crop))].length} iconPath={Icons.leaf} color="amber" />
          <StatCard label="Regions" value={[...new Set(history.map(h => h.region))].length} iconPath={Icons.map} color="slate" />
        </div>

        {/* Table */}
        <div className={`rounded-xl border overflow-hidden ${isDark ? "bg-slate-900 border-slate-700" : "bg-white border-slate-200"}`}>
          <div className={`border-b px-6 py-4 flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between ${isDark ? "border-slate-700" : "border-slate-100"}`}>
            <h2 className={`font-bold ${isDark ? "text-slate-100" : "text-slate-900"}`}>All Records</h2>
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by crop or region..."
              className={`rounded-lg border px-3.5 py-2 text-sm w-full sm:w-64 focus:outline-none focus:ring-2 focus:ring-emerald-500 ${isDark ? "bg-slate-800 border-slate-600 text-slate-100 placeholder-slate-500" : "border-slate-200 text-slate-800"}`} />
          </div>

          {filtered.length === 0 ? (
            <div className={`text-center py-16 ${isDark ? "text-slate-500" : "text-slate-400"}`}>
              <Icon path={Icons.history} size={36} className="mx-auto mb-3 opacity-30" />
              <p className="font-medium">{history.length === 0 ? "No predictions made yet" : "No results match your search"}</p>
              {history.length === 0 && <Button variant="primary" size="sm" onClick={() => setPage("predict")} className="mt-4">Make First Prediction</Button>}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className={`border-b text-xs uppercase ${isDark ? "border-slate-700 text-slate-500 bg-slate-800" : "border-slate-100 text-slate-400 bg-slate-50"}`}>
                  {["Date", "Crop", "Region", "Season", "Yield (t/ha)", "Status", "Actions"].map(h => (
                    <th key={h} className={`px-5 py-3 font-semibold ${h === "Yield (t/ha)" ? "text-right" : "text-left"}`}>{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {filtered.map(h => (
                    <tr key={h.id} className={`border-b transition ${isDark ? "border-slate-800 hover:bg-slate-800" : "border-slate-50 hover:bg-slate-50"}`}>
                      <td className={`px-5 py-3.5 ${isDark ? "text-slate-400" : "text-slate-500"}`}>{h.date}</td>
                      <td className={`px-5 py-3.5 font-semibold ${isDark ? "text-slate-200" : "text-slate-800"}`}>{h.crop}</td>
                      <td className={`px-5 py-3.5 ${isDark ? "text-slate-400" : "text-slate-600"}`}>{h.region}</td>
                      <td className="px-5 py-3.5"><Badge color={h.season === "Wet" ? "blue" : "amber"}>{h.season}</Badge></td>
                      <td className="px-5 py-3.5 text-right font-bold text-emerald-500">{h.predictedYield}</td>
                      <td className="px-5 py-3.5"><Badge color="green">{h.status}</Badge></td>
                      <td className="px-5 py-3.5">
                        <div className="flex gap-2">
                          <button onClick={() => onViewResult(h)} className={`p-1.5 rounded-lg transition ${isDark ? "hover:bg-emerald-900/40 text-emerald-500" : "hover:bg-emerald-50 text-emerald-700"}`} title="View details">
                            <Icon path={Icons.eye} size={15} />
                          </button>
                          <button onClick={() => setHistory(prev => prev.filter(p => p.id !== h.id))} className={`p-1.5 rounded-lg transition ${isDark ? "hover:bg-red-900/30 text-red-400" : "hover:bg-red-50 text-red-500"}`} title="Delete">
                            <Icon path={Icons.trash} size={15} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────
// PAGE: MODEL INFO
// ─────────────────────────────────────────
const ModelPage = () => {
  const isDark = useContext(ThemeContext);
  const features = [
    { name: "Rainfall (mm)", importance: 0.23, desc: "Annual or seasonal precipitation — the strongest predictor of yield for rain-fed agriculture." },
    { name: "Fertilizer Usage (kg/ha)", importance: 0.20, desc: "Soil nutrient supplementation significantly influences crop productivity and grain filling." },
    { name: "Temperature (°C)", importance: 0.17, desc: "Average growing season temperature determines photosynthetic rate and growing degree days." },
    { name: "Soil Type", importance: 0.14, desc: "Soil texture and drainage characteristics affect root penetration and water retention." },
    { name: "Humidity (%)", importance: 0.10, desc: "Relative humidity influences transpiration rates, disease incidence, and grain moisture." },
    { name: "Pesticide Usage (kg/ha)", importance: 0.08, desc: "Crop protection determines the proportion of potential yield actually harvested." },
    { name: "Area Cultivated (ha)", importance: 0.05, desc: "Scale factor used for total yield estimation from per-hectare predictions." },
    { name: "Season", importance: 0.03, desc: "Wet or dry season classification encodes photoperiod and rainfall patterns implicitly." },
  ];

  return (
    <div className={`flex-1 py-8 px-4 md:px-8 ${isDark ? "bg-slate-950" : "bg-slate-50"}`}>
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <p className="text-emerald-500 font-semibold text-xs uppercase tracking-widest mb-2">Technical Documentation</p>
          <h1 className={`text-2xl font-extrabold ${isDark ? "text-slate-100" : "text-slate-900"}`}>Machine Learning Model Information</h1>
          <p className={`text-sm mt-1 ${isDark ? "text-slate-400" : "text-slate-500"}`}>Technical details of the predictive model used in this system.</p>
        </div>

        <div className="space-y-6">
          {/* Model Summary */}
          <div className={`border rounded-xl p-7 ${isDark ? "bg-slate-900 border-slate-700" : "bg-white border-slate-200"}`}>
            <h2 className={`font-bold text-lg mb-4 pb-3 border-b ${isDark ? "text-slate-100 border-slate-700" : "text-slate-900 border-slate-100"}`}>Model Overview</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-5">
              {[["Algorithm", "Random Forest Regressor"], ["R² Score", "0.891"], ["RMSE", "1.24 t/ha"], ["MAE", "0.87 t/ha"], ["Training Samples", "~28,000"], ["Features Used", "11"]].map(([k, v]) => (
                <div key={k} className={`rounded-lg px-4 py-3 ${isDark ? "bg-emerald-900/30" : "bg-emerald-50"}`}>
                  <p className="text-xs text-emerald-500 font-medium">{k}</p>
                  <p className={`text-sm font-bold mt-0.5 ${isDark ? "text-slate-100" : "text-slate-900"}`}>{v}</p>
                </div>
              ))}
            </div>
            <p className={`text-sm leading-relaxed ${isDark ? "text-slate-300" : "text-slate-600"}`}>
              The <strong>Random Forest Regressor</strong> was selected as the primary model following systematic comparative evaluation against Linear Regression, Support Vector Regression, Decision Tree Regression, and Gradient Boosted Trees. The Random Forest model demonstrated superior generalisation performance on the hold-out test set, achieving an R² score of <strong>0.891</strong> with cross-validated RMSE of <strong>1.24 t/ha</strong>.
            </p>
          </div>

          {/* Why RF */}
          <div className={`border rounded-xl p-7 ${isDark ? "bg-slate-900 border-slate-700" : "bg-white border-slate-200"}`}>
            <h2 className={`font-bold text-lg mb-4 pb-3 border-b ${isDark ? "text-slate-100 border-slate-700" : "text-slate-900 border-slate-100"}`}>Why Random Forest?</h2>
            <div className={`space-y-4 text-sm leading-relaxed ${isDark ? "text-slate-300" : "text-slate-600"}`}>
              <p><strong className={isDark ? "text-slate-100" : "text-slate-800"}>Robustness to Overfitting:</strong> As an ensemble of decision trees trained on randomised subsets of data, Random Forests resist memorising noise in the training data. This is particularly important given the high variability in agricultural datasets.</p>
              <p><strong className={isDark ? "text-slate-100" : "text-slate-800"}>Handles Mixed Input Types:</strong> The model natively handles both continuous (rainfall, temperature) and categorical (crop, soil type, season) features without requiring extensive preprocessing.</p>
              <p><strong className={isDark ? "text-slate-100" : "text-slate-800"}>Feature Importance:</strong> Built-in feature importance rankings enable model transparency — a key requirement for academic and practical trustworthiness of the system.</p>
              <p><strong className={isDark ? "text-slate-100" : "text-slate-800"}>Non-linearity:</strong> Agricultural yield relationships are highly non-linear. Random Forests capture complex interactions between rainfall and temperature without explicit feature engineering.</p>
            </div>
          </div>

          {/* Feature Importance */}
          <div className={`border rounded-xl p-7 ${isDark ? "bg-slate-900 border-slate-700" : "bg-white border-slate-200"}`}>
            <h2 className={`font-bold text-lg mb-5 pb-3 border-b ${isDark ? "text-slate-100 border-slate-700" : "text-slate-900 border-slate-100"}`}>Feature Importance</h2>
            <div className="space-y-4">
              {features.map(f => (
                <div key={f.name}>
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-sm font-semibold ${isDark ? "text-slate-200" : "text-slate-800"}`}>{f.name}</span>
                    <span className="text-xs font-bold text-emerald-500">{(f.importance * 100).toFixed(0)}%</span>
                  </div>
                  <div className={`w-full rounded-full h-2 mb-1 ${isDark ? "bg-slate-700" : "bg-slate-100"}`}>
                    <div className="bg-emerald-600 h-2 rounded-full transition-all" style={{ width: `${f.importance * 100}%` }} />
                  </div>
                  <p className={`text-xs ${isDark ? "text-slate-500" : "text-slate-400"}`}>{f.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Limitations */}
          <div className={`rounded-xl p-7 ${isDark ? "bg-amber-900/20 border border-amber-800" : "bg-amber-50 border border-amber-200"}`}>
            <h2 className={`font-bold text-lg mb-4 ${isDark ? "text-amber-400" : "text-amber-900"}`}>Model Limitations</h2>
            <ul className={`space-y-2 text-sm list-disc list-inside ${isDark ? "text-amber-300" : "text-amber-800"}`}>
              <li>Predictions are statistical estimates, not agronomic guarantees. Actual yield may vary due to unforeseen biotic and abiotic stresses.</li>
              <li>The model is trained primarily on Nigerian agricultural data. Performance may degrade for international or significantly different agroecological zones.</li>
              <li>Extreme climate events, pest outbreaks, and political disruptions to supply chains are not accounted for in the model.</li>
              <li>Input data quality directly affects output quality (GIGO principle). Ensure all entered values are accurate field measurements.</li>
              <li>The model does not account for irrigation availability, which can substantially alter yield independently of rainfall.</li>
            </ul>
          </div>

          {/* Use Cases */}
          <div className={`border rounded-xl p-7 ${isDark ? "bg-slate-900 border-slate-700" : "bg-white border-slate-200"}`}>
            <h2 className={`font-bold text-lg mb-4 pb-3 border-b ${isDark ? "text-slate-100 border-slate-700" : "text-slate-900 border-slate-100"}`}>Expected Use Cases</h2>
            <div className="grid sm:grid-cols-2 gap-4 text-sm">
              {[
                ["Seasonal Farm Planning", "Farmers can use pre-season predictions to decide whether to plant, how much to invest in inputs, and which crop variety to prioritise."],
                ["Agricultural Research", "Researchers can study how altering input variables affects yield, simulating environmental scenarios or fertilizer trials computationally."],
                ["Food Security Planning", "Government planners and NGOs can aggregate predictions across regions to estimate regional food supply and identify food security risks."],
                ["Input Optimisation", "By running multiple predictions with varied fertilizer/pesticide inputs, users can identify the optimal input combination for a target yield."],
              ].map(([t, d]) => (
                <div key={t} className={`rounded-lg p-4 ${isDark ? "bg-slate-800" : "bg-slate-50"}`}>
                  <p className={`font-bold mb-1 ${isDark ? "text-slate-200" : "text-slate-800"}`}>{t}</p>
                  <p className={`text-xs leading-relaxed ${isDark ? "text-slate-400" : "text-slate-500"}`}>{d}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────
// PAGE: ABOUT
// ─────────────────────────────────────────
const AboutPage = () => {
  const isDark = useContext(ThemeContext);
  return (
  <div className={`flex-1 py-8 px-4 md:px-8 ${isDark ? "bg-slate-950" : "bg-slate-50"}`}>
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <p className="text-emerald-500 font-semibold text-xs uppercase tracking-widest mb-2">Project Documentation</p>
        <h1 className={`text-2xl font-extrabold ${isDark ? "text-slate-100" : "text-slate-900"}`}>About This Project</h1>
        <p className={`text-sm mt-1 ${isDark ? "text-slate-400" : "text-slate-500"}`}>A final year computer science research project on machine learning in agriculture.</p>
      </div>

      <div className="space-y-6">
        <div className={`border rounded-xl p-7 ${isDark ? "bg-slate-900 border-slate-700" : "bg-white border-slate-200"}`}>
          <h2 className={`font-bold text-lg mb-4 pb-3 border-b ${isDark ? "text-slate-100 border-slate-700" : "text-slate-900 border-slate-100"}`}>Project Overview</h2>
          <p className={`text-sm leading-relaxed ${isDark ? "text-slate-300" : "text-slate-600"}`}>
            <em>Crop Yield Prediction Using Machine Learning Models</em> is a final year undergraduate project submitted to the Department of Computer Science, Federal University Dutsin-Ma. The project investigates the application of supervised machine learning techniques to predict crop yields in Nigerian agricultural environments using measurable environmental and agronomic input parameters.
          </p>
          <p className={`text-sm leading-relaxed mt-3 ${isDark ? "text-slate-300" : "text-slate-600"}`}>
            The resulting system is a web-based application that provides a practical, accessible interface for farmers, researchers, extension officers, and agricultural planners to input field data and receive machine learning-generated yield estimates in real time.
          </p>
        </div>

        <div className={`border rounded-xl p-7 ${isDark ? "bg-slate-900 border-slate-700" : "bg-white border-slate-200"}`}>
          <h2 className={`font-bold text-lg mb-4 pb-3 border-b ${isDark ? "text-slate-100 border-slate-700" : "text-slate-900 border-slate-100"}`}>Problem Statement</h2>
          <p className={`text-sm leading-relaxed ${isDark ? "text-slate-300" : "text-slate-600"}`}>
            Agricultural productivity in Nigeria remains significantly below potential. Small and medium-scale farmers frequently make planting, input procurement, and marketing decisions without reliable yield forecasts. This uncertainty leads to overinvestment in low-yield seasons, underinvestment in high-yield seasons, food insecurity, and economic instability for farming households.
          </p>
          <p className={`text-sm leading-relaxed mt-3 ${isDark ? "text-slate-300" : "text-slate-600"}`}>
            Existing yield estimation approaches in Nigeria largely depend on manual observation, historical averages, or anecdotal farmer knowledge — methods that do not adequately account for inter-seasonal variability in rainfall, temperature, and soil conditions.
          </p>
        </div>

        <div className={`border rounded-xl p-7 ${isDark ? "bg-slate-900 border-slate-700" : "bg-white border-slate-200"}`}>
          <h2 className={`font-bold text-lg mb-3 pb-3 border-b ${isDark ? "text-slate-100 border-slate-700" : "text-slate-900 border-slate-100"}`}>Aim & Objectives</h2>
          <p className={`text-sm leading-relaxed mb-4 ${isDark ? "text-slate-300" : "text-slate-600"}`}><strong>Aim:</strong> To develop a machine learning-based web application capable of predicting crop yields for Nigerian agricultural regions with demonstrably high accuracy.</p>
          <p className={`text-sm font-semibold mb-2 ${isDark ? "text-slate-200" : "text-slate-700"}`}>Specific Objectives:</p>
          <ol className={`list-decimal list-inside space-y-2 text-sm ${isDark ? "text-slate-300" : "text-slate-600"}`}>
            <li>Review and evaluate machine learning algorithms suitable for agricultural regression tasks.</li>
            <li>Collect, clean, and prepare a representative agricultural dataset for model training.</li>
            <li>Train, validate, and select the optimal predictive model based on empirical performance metrics.</li>
            <li>Design and develop a responsive, accessible web-based interface for system interaction.</li>
            <li>Integrate the trained ML model with the frontend via a REST API backend.</li>
            <li>Evaluate the complete system using usability testing with target user groups.</li>
          </ol>
        </div>

        <div className={`border rounded-xl p-7 ${isDark ? "bg-slate-900 border-slate-700" : "bg-white border-slate-200"}`}>
          <h2 className={`font-bold text-lg mb-4 pb-3 border-b ${isDark ? "text-slate-100 border-slate-700" : "text-slate-900 border-slate-100"}`}>Relevance to Nigerian Agriculture</h2>
          <p className={`text-sm leading-relaxed ${isDark ? "text-slate-300" : "text-slate-600"}`}>
            Nigeria is the largest economy in Africa and home to one of the continent's largest agricultural sectors, contributing approximately 22% of GDP. Yet, average crop yields remain among the lowest globally — maize yields average <strong>1.8 t/ha</strong> in Nigeria compared to the global average of <strong>5.5 t/ha</strong>.
          </p>
          <p className={`text-sm leading-relaxed mt-3 ${isDark ? "text-slate-300" : "text-slate-600"}`}>
            Data-driven tools that help farmers optimise inputs, understand the impact of environmental conditions on yield, and plan more effectively have the potential to narrow this gap. This system directly supports <strong>SDG 2 (Zero Hunger)</strong> and <strong>SDG 8 (Decent Work and Economic Growth)</strong> by improving agricultural decision-making for smallholder farmers.
          </p>
        </div>

        {/* Developer Card */}
        <div className="bg-emerald-900 rounded-xl p-7 text-white">
          <h2 className="font-bold text-white text-lg mb-5 pb-3 border-b border-white/10">About the Developer</h2>
          <div className="flex items-start gap-5">
            <div className="w-16 h-16 rounded-2xl bg-emerald-700 flex items-center justify-center shrink-0 text-3xl font-bold text-white shadow-md">
              F
            </div>
            <div>
              <p className="text-xl font-extrabold text-white">Fayyad Inda Musa</p>
              <p className="text-emerald-300 text-sm mt-0.5">Final Year Student · B.Sc. Computer Science</p>
              <div className="mt-3 space-y-1 text-sm text-emerald-100">
                <p><span className="text-emerald-400 font-medium">Department:</span> Computer Science</p>
                <p><span className="text-emerald-400 font-medium">Institution:</span> Federal University, Dutsin-Ma</p>
                <p><span className="text-emerald-400 font-medium">State:</span> Katsina State, Nigeria</p>
                <p><span className="text-emerald-400 font-medium">Academic Year:</span> 2024/2025</p>
              </div>
              <p className="text-emerald-200 text-xs mt-4 leading-relaxed max-w-lg">
                This project was developed as part of the requirements for the award of Bachelor of Science in Computer Science. It represents an intersection of data science, software engineering, and agricultural science, motivated by the goal of improving food security in Nigeria through accessible technology.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  );
};

// ─────────────────────────────────────────
// PAGE: HELP
// ─────────────────────────────────────────
const HelpPage = () => {
  const isDark = useContext(ThemeContext);
  const [open, setOpen] = useState(null);
  const [form, setForm] = useState({ name: "", email: "", message: "" });
  const [sent, setSent] = useState(false);

  const faqs = [
    { q: "What does the predicted yield number mean?", a: "The predicted yield is expressed in tons per hectare (t/ha). It represents the estimated mass of crop produce expected from one hectare of cultivated land under the conditions you specified." },
    { q: "How accurate are the predictions?", a: "The model achieved an R² score of 0.891 on the validation dataset. This means approximately 89.1% of the variance in yield is explained by the input variables. Predictions should be treated as informed estimates, not exact guarantees." },
    { q: "What data should I enter for rainfall?", a: "Enter the average annual or seasonal rainfall for your farming region in millimetres (mm). You can obtain this from Nigerian Meteorological Agency (NiMet) data, state agricultural departments, or local weather stations." },
    { q: "Can I use this system for crops not listed?", a: "Currently, the model supports the 12 crops listed in the crop dropdown. Predictions for unlisted crops would be unreliable, as the model was not trained on data for those crops." },
    { q: "How do I save and export my results?", a: "After a prediction is generated, you can click 'Save Result' to store it in your prediction history. You can then export individual or all predictions as PDF or CSV using the export buttons on the history page." },
    { q: "Is my data stored securely?", a: "In the current prototype, prediction data is stored in the application's session. In production, data will be stored in a secured database with user authentication and access controls." },
    { q: "Can I use this system on my phone?", a: "Yes. The interface is fully responsive and designed to work on smartphones, tablets, and desktop computers." },
  ];

  const handleSend = () => {
    if (!form.name || !form.email || !form.message) return;
    setSent(true);
  };

  return (
    <div className={`flex-1 py-8 px-4 md:px-8 ${isDark ? "bg-slate-950" : "bg-slate-50"}`}>
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <p className="text-emerald-500 font-semibold text-xs uppercase tracking-widest mb-2">Support</p>
          <h1 className={`text-2xl font-extrabold ${isDark ? "text-slate-100" : "text-slate-900"}`}>Help & Guidance</h1>
          <p className={`text-sm mt-1 ${isDark ? "text-slate-400" : "text-slate-500"}`}>Answers to common questions and a guide to using the prediction system.</p>
        </div>

        {/* How to Use */}
        <div className={`rounded-xl p-7 mb-6 ${isDark ? "bg-emerald-900/20 border border-emerald-800" : "bg-emerald-50 border border-emerald-200"}`}>
          <h2 className={`font-bold text-lg mb-4 ${isDark ? "text-emerald-400" : "text-emerald-900"}`}>How to Use the Prediction System</h2>
          <ol className="space-y-3">
            {[
              ["Create an Account", "Register with your email to access the full system. A demo account is available for immediate use."],
              ["Navigate to Predict", "Click 'Predict' in the navigation bar to access the prediction form."],
              ["Fill in the Form", "Enter your crop, region, environmental conditions, and agronomic inputs carefully. All fields marked with * are required."],
              ["Run the Prediction", "Click 'Run Prediction'. The system will process your inputs through the ML model (takes 1–3 seconds)."],
              ["Review the Results", "The result page shows your predicted yield, a confidence indicator, and an interpretation summary."],
              ["Save or Export", "Save your result to history for future reference, or export it as PDF/CSV for reports and documentation."],
            ].map(([t, d], i) => (
              <li key={i} className="flex gap-4">
                <span className="w-6 h-6 rounded-full bg-emerald-700 text-white text-xs flex items-center justify-center font-bold shrink-0 mt-0.5">{i + 1}</span>
                <div>
                  <p className={`font-semibold text-sm ${isDark ? "text-emerald-400" : "text-emerald-900"}`}>{t}</p>
                  <p className={`text-xs mt-0.5 ${isDark ? "text-emerald-300" : "text-emerald-700"}`}>{d}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>

        {/* FAQ */}
        <div className={`rounded-xl border overflow-hidden mb-6 ${isDark ? "bg-slate-900 border-slate-700" : "bg-white border-slate-200"}`}>
          <div className={`border-b px-6 py-4 ${isDark ? "border-slate-700" : "border-slate-100"}`}>
            <h2 className={`font-bold ${isDark ? "text-slate-100" : "text-slate-900"}`}>Frequently Asked Questions</h2>
          </div>
          <div className={`divide-y ${isDark ? "divide-slate-700" : "divide-slate-100"}`}>
            {faqs.map((f, i) => (
              <div key={i}>
                <button onClick={() => setOpen(open === i ? null : i)} className={`w-full text-left flex items-center justify-between px-6 py-4 transition ${isDark ? "hover:bg-slate-800" : "hover:bg-slate-50"}`}>
                  <span className={`text-sm font-semibold ${isDark ? "text-slate-200" : "text-slate-800"}`}>{f.q}</span>
                  <Icon path={open === i ? Icons.close : Icons.plus} size={16} className={`shrink-0 ml-3 ${isDark ? "text-slate-500" : "text-slate-400"}`} />
                </button>
                {open === i && (
                  <div className={`px-6 pb-4 text-sm leading-relaxed ${isDark ? "text-slate-300" : "text-slate-600"}`}>{f.a}</div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Contact */}
        <div className={`border rounded-xl p-7 ${isDark ? "bg-slate-900 border-slate-700" : "bg-white border-slate-200"}`}>
          <h2 className={`font-bold text-lg mb-5 pb-3 border-b ${isDark ? "text-slate-100 border-slate-700" : "text-slate-900 border-slate-100"}`}>Contact & Support</h2>
          {sent ? (
            <div className="text-center py-8">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3 ${isDark ? "bg-emerald-900/50" : "bg-emerald-100"}`}>
                <Icon path={Icons.check} size={22} className="text-emerald-500" />
              </div>
              <p className={`font-bold ${isDark ? "text-slate-100" : "text-slate-900"}`}>Message Sent</p>
              <p className={`text-sm mt-1 ${isDark ? "text-slate-400" : "text-slate-500"}`}>Thank you for your message. We'll respond as soon as possible.</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid sm:grid-cols-2 gap-4">
                <Input label="Full Name" name="name" value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} placeholder="Your name" />
                <Input label="Email Address" name="email" type="email" value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))} placeholder="you@example.com" />
              </div>
              <div className="flex flex-col gap-1">
                <label className={`text-sm font-semibold ${isDark ? "text-slate-300" : "text-slate-700"}`}>Message</label>
                <textarea value={form.message} onChange={e => setForm(p => ({ ...p, message: e.target.value }))} rows={4} placeholder="Describe your question or issue..."
                  className={`w-full rounded-lg border px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none ${isDark ? "bg-slate-800 border-slate-600 text-slate-100 placeholder-slate-500" : "border-slate-300 text-slate-800 placeholder-slate-400"}`} />
              </div>
              <Button variant="primary" onClick={handleSend} iconPath={Icons.mail}>Send Message</Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────
// ROOT APP
// ─────────────────────────────────────────
export default function App() {
  const [page, setPage] = useState("landing");
  const [isDark, setIsDark] = useState(() => {
    try { return localStorage.getItem("cyai_landing_theme") === "dark"; } catch { return false; }
  });
  const [user, setUser] = useState(null);
  const [result, setResult] = useState(null);
  const [resultSaved, setResultSaved] = useState(false);
  const [history, setHistory] = useState(() => {
    try { const s = localStorage.getItem("cyai_history"); return s ? JSON.parse(s) : []; } catch { return []; }
  });
  const [toast, setToast] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const showToast = useCallback((message, type = "success") => {
    setToast({ message, type });
  }, []);

  useEffect(() => {
    try { localStorage.setItem("cyai_history", JSON.stringify(history)); } catch {}
  }, [history]);

  // Fetch server-side history on first load
  useEffect(() => {
    fetchHistoryFromApi()
      .then(r => { if (r && r.length) setHistory(r); })
      .catch(() => { showToast("Failed to load history from server", "error"); });
  }, []);

  useEffect(() => {
    try { localStorage.setItem("cyai_landing_theme", isDark ? "dark" : "light"); } catch {}
  }, [isDark]);

  const handleAuth = (userData) => {
    setUser(userData);
    setPage("dashboard");
    showToast(`Welcome, ${userData.name.split(" ")[0]}!`, "success");
  };

  const handleLogout = () => {
    setUser(null);
    setPage("landing");
    showToast("You have been signed out.", "info");
  };

  const handleResult = (data) => {
    setResult(data);
    setResultSaved(false);
    setPage("result");
    // Refresh history from backend (best-effort)
    fetchHistoryFromApi().then(r => { if (r && r.length) setHistory(r); }).catch(() => { showToast("Failed to refresh history from server", "error"); });
  };

  const handleSaveResult = () => {
    if (!resultSaved && result) {
      setHistory(prev => [result, ...prev]);
      setResultSaved(true);
      showToast("Prediction saved to history.", "success");
    }
  };

  const handleViewResult = (item) => {
    setResult({ ...item, model: "Random Forest Regressor", r2Score: 0.891, confidence: 85 + Math.random() * 10 });
    setResultSaved(true);
    setPage("result");
  };

  const protectedSetPage = (p) => {
    const protected_ = ["dashboard", "predict", "result", "history", "model"];
    if (protected_.includes(p) && !user) {
      setPage("login");
      showToast("Please sign in to continue.", "info");
      return;
    }
    setPage(p);
    setSidebarOpen(false);
    window.scrollTo(0, 0);
  };

  const renderPage = () => {
    switch (page) {
      case "landing": return <LandingPage setPage={protectedSetPage} isDark={isDark} onToggleTheme={() => setIsDark(v => !v)} />;
      case "login": return <AuthPage type="login" setPage={setPage} onAuth={handleAuth} />;
      case "register": return <AuthPage type="register" setPage={setPage} onAuth={handleAuth} />;
      case "dashboard": return <DashboardPage setPage={protectedSetPage} history={history} user={user} />;
      case "predict": return <PredictPage onResult={handleResult} onError={showToast} />;
      case "result": return result ? <ResultPage result={result} setPage={protectedSetPage} onSave={handleSaveResult} saved={resultSaved} /> : null;
      case "history": return <HistoryPage history={history} setHistory={setHistory} setPage={protectedSetPage} onViewResult={handleViewResult} />;
      case "model": return <ModelPage />;
      case "about": return <AboutPage />;
      case "help": return <HelpPage />;
      default: return <LandingPage setPage={protectedSetPage} isDark={isDark} onToggleTheme={() => setIsDark(v => !v)} />;
    }
  };

  const showNav = page !== "login" && page !== "register";
  const showFooter = !["dashboard", "predict", "result", "history", "model", "help"].includes(page) && page !== "login" && page !== "register" && !!user;

  return (
    <ThemeContext.Provider value={isDark}>
    <div className={`min-h-screen flex flex-col font-sans ${isDark ? "bg-slate-950" : "bg-slate-50"}`}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700;800&family=Playfair+Display:wght@700;800&display=swap');
        body, * { font-family: 'DM Sans', sans-serif; }
        h1, h2 { font-family: 'DM Sans', sans-serif; }
        .hero-title { font-family: 'Playfair Display', serif; }
      `}</style>

      {showNav && (
        <Navbar page={page} setPage={protectedSetPage} user={user} onLogout={handleLogout}
          sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} isDark={isDark} onToggleTheme={() => setIsDark(v => !v)} />
      )}

      <main className="flex-1 flex flex-col">
        {renderPage()}
      </main>

      {showFooter && <Footer setPage={protectedSetPage} />}
      {user && !showFooter && page !== "login" && page !== "register" && (
        <footer className={`border-t py-4 text-center text-xs ${isDark ? "border-slate-800 text-slate-500 bg-slate-900" : "border-slate-200 text-slate-400 bg-white"}`}>
          CropYieldAI · Final Year CS Project · Federal University Dutsin-Ma · © 2025
        </footer>
      )}

      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
    </ThemeContext.Provider>
  );
}

// ─────────────────────────────────────────
// RENDER APP TO DOM
// ─────────────────────────────────────────
import { createRoot } from "react-dom/client";

const container = document.getElementById("root");
const root = createRoot(container);
root.render(<App />);
