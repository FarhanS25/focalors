import { lazy, Suspense, useEffect } from "react";

import Navbar from "./components/layout/Navbar";
import Footer from "./components/layout/Footer";
import Hero from "./components/home/Hero";
import Features from "./components/home/Features";
import HowItWorks from "./components/home/HowItWorks";
import Mission from "./components/home/Mission";

const Dashboard = lazy(() => import("./Dashboard.jsx"));

function ScrollToTop() {
  useEffect(() => {
    window.history.scrollRestoration = "manual";
    window.scrollTo(0, 0);
  }, []);

  return null;
}

function LandingPage() {
  return (
    <>
      <ScrollToTop />
      <Navbar />

      <main className="min-h-screen bg-[#071C2B] text-white">
        <Hero />
        <Features />
        <HowItWorks />

        <div className="relative isolate bg-[#071C2B]">
          <Mission />
          <Footer />
        </div>
      </main>
    </>
  );
}

export default function App() {
  const path = window.location.pathname.replace(/\/+$/, "") || "/";
  if (path === "/investigate") {
    return (
      <Suspense fallback={null}>
        <Dashboard />
      </Suspense>
    );
  }
  return <LandingPage />;
}
