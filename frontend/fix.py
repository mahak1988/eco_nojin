import structlog

logger = structlog.get_logger()
import os
base = "D:/eco_nojin/frontend/src"

# Dirs
for d in ["components/layout", "pages", "styles"]:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# App.tsx
open(os.path.join(base, "App.tsx"), "w").write("""import { ConfigProvider, theme } from "antd";
import { faIR } from "antd/es/locale/fa_IR";
import AppLayout from "./components/layout/AppLayout";

function App() {
  return (
    <ConfigProvider locale={faIR} theme={{ algorithm: theme.defaultAlgorithm }}>
      <AppLayout />
    </ConfigProvider>
  );
}
export default App;
""")

# Layout
open(os.path.join(base, "components/layout/AppLayout.tsx"), "w").write("""import { useState } from "react";
import { Layout, Menu, Typography, Button, Avatar, Space } from "antd";
import { DashboardOutlined, ExperimentOutlined, EnvironmentOutlined, BarChartOutlined, ApiOutlined, SettingOutlined, MenuFoldOutlined, MenuUnfoldOutlined } from "@ant-design/icons";

const { Header, Sider, Content, Footer } = Layout;
const { Title } = Typography;

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed} width={260}
        style={{ background: "#001529" }}>
        <div style={{ height: 64, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Title level={4} style={{ color: "#fff", margin: 0 }}>HYDROMA</Title>
        </div>
        <Menu mode="inline" items={[
          { key: "dash", icon: <DashboardOutlined />, label: "Dashboard" },
          { key: "sim", icon: <ExperimentOutlined />, label: "Simulation" },
          { key: "land", icon: <EnvironmentOutlined />, label: "Land & Soil" },
          { key: "vis", icon: <BarChartOutlined />, label: "Visualization" }
        ]} defaultSelectedKeys={["dash"]} style={{ background: "transparent", color: "#fff" }} theme={{ dark: true }} />
      </Sider>
      <Layout>
        <Header style={{ background: "#fff", padding: "0 24px", display: "flex", justifyContent: "space-between" }}>
          <Button type="text" onClick={() => setCollapsed(!collapsed)}>{collapsed ? ">" : "<"}</Button>
          <Avatar style={{ backgroundColor: "#1677ff" }}>U</Avatar>
        </Header>
        <Content style={{ margin: 24 }}><h1>Welcome to HYDROMA</h1></Content>
        <Footer style={{ textAlign: "center" }}>HYDROMA</Footer>
      </Layout>
    </Layout>
  );
}
""")

# CSS
open(os.path.join(base, "styles/global.css"), "w").write("body{margin:0;direction:rtl;font-family:sans-serif}")

# main.tsx  
open(os.path.join(base, "main.tsx"), "w").write("""import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/global.css";
ReactDOM.createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
""")

logger.info("All files created!")
