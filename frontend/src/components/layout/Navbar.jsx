import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { ArrowRight, Droplets, Menu, X } from "lucide-react";

const navLinks = [
  { label: "Home", href: "#home" },
  { label: "Features", href: "#features" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "Our Mission", href: "#mission" },
];

function Navbar() {
  const [visible, setVisible] = useState(true);
  const [activeSection, setActiveSection] = useState("home");
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const shouldReduceMotion = useReducedMotion();

  // Smoothly navigate to a section without hiding the navbar.
  const handleSmoothScroll = (event, href) => {
    if (!href.startsWith("#")) return;

    const target = document.querySelector(href);
    if (!target) return;

    event.preventDefault();

    setVisible(true);
    setMenuOpen(false);

    const targetPosition = target.getBoundingClientRect().top + window.scrollY - 88;

    window.history.replaceState(null, "", href);

    window.scrollTo({
      top: targetPosition,
      behavior: shouldReduceMotion ? "instant" : "smooth",
    });
  };

  // Hide on downward scrolling, except during navigation.
  useEffect(() => {
    let lastScrollY = window.scrollY;
    let ticking = false;
    let navigationClicked = false;
    let navigationTimeout;

    const handleNavigationClick = (event) => {
      const link = event.target.closest('a[href^="#"]');

      if (!link) return;

      navigationClicked = true;
      setVisible(true);

      clearTimeout(navigationTimeout);

      navigationTimeout = setTimeout(() => {
        navigationClicked = false;
        lastScrollY = window.scrollY;
      }, 1200);
    };

    const handleScroll = () => {
      if (ticking) return;

      ticking = true;

      window.requestAnimationFrame(() => {
        const currentScrollY = window.scrollY;
        const difference = currentScrollY - lastScrollY;

        setScrolled(currentScrollY > 20);

        if (navigationClicked || currentScrollY < 80) {
          setVisible(true);
        } else if (difference > 3) {
          setVisible(false);
        } else if (difference < -3) {
          setVisible(true);
        }

        lastScrollY = currentScrollY;
        ticking = false;
      });
    };

    document.addEventListener("click", handleNavigationClick);
    window.addEventListener("scroll", handleScroll, { passive: true });

    return () => {
      document.removeEventListener("click", handleNavigationClick);
      window.removeEventListener("scroll", handleScroll);
      clearTimeout(navigationTimeout);
    };
  }, []);

  // Highlight the navigation link for the section currently in view.
  useEffect(() => {
    const sections = navLinks
      .map((link) => document.getElementById(link.href.slice(1)))
      .filter(Boolean);

    if (!sections.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const current = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

        if (current) {
          setActiveSection(current.target.id);
        }
      },
      {
        rootMargin: "-20% 0px -55% 0px",
        threshold: [0, 0.1, 0.25, 0.5],
      },
    );

    sections.forEach((section) => observer.observe(section));

    return () => observer.disconnect();
  }, []);

  return (
    <motion.header
      initial={shouldReduceMotion ? false : { y: -90, opacity: 0 }}
      animate={{
        y: visible ? 0 : "-100%",
        opacity: visible ? 1 : 0,
      }}
      transition={{
        duration: shouldReduceMotion ? 0 : 0.35,
        ease: [0.22, 1, 0.36, 1],
      }}
      className={`home-nav fixed left-0 top-0 z-50 w-full ${scrolled ? "shadow-[0_18px_40px_rgba(0,0,0,0.28)]" : ""}`}
    >
      <nav className="home-wrap flex h-[76px] items-center justify-between gap-4">
        <motion.a
          href="#home"
          onClick={(event) => handleSmoothScroll(event, "#home")}
          aria-label="FOCALORS home"
          className="home-brand shrink-0"
          whileHover={shouldReduceMotion ? undefined : { scale: 1.02 }}
          whileTap={shouldReduceMotion ? undefined : { scale: 0.98 }}
          transition={{ duration: 0.2 }}
        >
          <span className="home-mark" aria-hidden="true">
            <Droplets size={20} />
          </span>
          <span>
            <b>FOCALORS <small>/ FIELD INTELLIGENCE</small></b>
            <p>Hydraulic leak investigation</p>
          </span>
        </motion.a>

        <div className={`home-links ${menuOpen ? "is-open" : ""}`}>
          {navLinks.map((link) => {
            const isActive = activeSection === link.href.slice(1);

            return (
              <a
                key={link.href}
                href={link.href}
                onClick={(event) => handleSmoothScroll(event, link.href)}
                aria-current={isActive ? "location" : undefined}
              >
                {link.label}
              </a>
            );
          })}
        </div>

        <div className="flex items-center gap-2">
          <a className="home-cta" href="/investigate">
            Open Investigation
            <ArrowRight size={16} />
          </a>
          <button
            type="button"
            className="home-menu-button"
            aria-expanded={menuOpen}
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </nav>
    </motion.header>
  );
}

export default Navbar;
