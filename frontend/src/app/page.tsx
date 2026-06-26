import { ConstellationField } from "../components/ConstellationField";
import { Dashboard } from "../components/dashboard/Dashboard";
import dashboardData from "../data/dashboard.json";
import type { DashboardData } from "../types/dashboard";

const data = dashboardData as DashboardData;

export default function Home() {
  return (
    <>
      <ConstellationField />
      <Dashboard data={data} />
    </>
  );
}
