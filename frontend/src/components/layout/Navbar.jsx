import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { ArrowRight } from "lucide-react";

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
  const [lightSection, setLightSection] = useState(false);

  const shouldReduceMotion = useReducedMotion();

  // Smoothly navigate to a section without hiding the navbar.
  const handleSmoothScroll = (event, href) => {
    if (!href.startsWith("#")) return;

    const target = document.querySelector(href);
    if (!target) return;

    event.preventDefault();

    setVisible(true);

    const targetPosition = target.getBoundingClientRect().top + window.scrollY;

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

  // Switch navbar colors over the light How It Works section.
  useEffect(() => {
    const section = document.getElementById("how-it-works");

    if (!section) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setLightSection(entry.isIntersecting);
      },
      {
        rootMargin: "-76px 0px -75% 0px",
        threshold: 0,
      },
    );

    observer.observe(section);

    return () => observer.disconnect();
  }, []);

  // Neutral charcoal glass over photographs; light glass over How It Works.
  const navbarTheme = lightSection
    ? "border-[#142A36]/10 bg-[#F1F5F7]/95 shadow-md shadow-black/5 backdrop-blur-xl"
    : "border-white/15 bg-[#101820]/75 shadow-md shadow-black/10 backdrop-blur-xl";

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
      className={`fixed left-0 top-0 z-50 w-full border-b transition-colors duration-300 ${navbarTheme}`}
    >
      <nav className="mx-auto flex h-[76px] max-w-7xl items-center justify-between px-6 lg:px-10">
        {/* Logo */}
        <motion.a
          href="#home"
          onClick={(event) => handleSmoothScroll(event, "#home")}
          aria-label="FOCALORS home"
          className="flex shrink-0 items-center"
          whileHover={shouldReduceMotion ? undefined : { scale: 1.035 }}
          whileTap={shouldReduceMotion ? undefined : { scale: 0.97 }}
          transition={{ duration: 0.2 }}
        >
          <img
            src="/images/logo.png"
            alt="FOCALORS"
            className="w-32 object-contain sm:w-36"
          />
        </motion.a>

        {/* Navigation links */}
        <div className="hidden items-center gap-6 lg:flex xl:gap-7">
          {navLinks.map((link) => {
            const isActive = activeSection === link.href.slice(1);

            const linkColor = lightSection
              ? isActive
                ? "text-[#008DB8]"
                : "text-[#203D4B] hover:text-[#008DB8]"
              : isActive
                ? "text-[#38BDF8]"
                : "text-white/90 hover:text-[#38BDF8]";

            return (
              <a
                key={link.href}
                href={link.href}
                onClick={(event) => handleSmoothScroll(event, link.href)}
                aria-current={isActive ? "location" : undefined}
                className={`group relative whitespace-nowrap py-2 text-sm font-semibold transition-colors duration-200 ${linkColor}`}
              >
                {link.label}

                {/* Animated active underline */}
                <motion.span
                  className={`absolute -bottom-0.5 left-0 h-[2px] rounded-full ${
                    lightSection ? "bg-[#008DB8]" : "bg-[#38BDF8]"
                  }`}
                  initial={false}
                  animate={{
                    width: isActive ? "100%" : "0%",
                    opacity: isActive ? 1 : 0,
                  }}
                  transition={{
                    duration: shouldReduceMotion ? 0 : 0.25,
                  }}
                />

                {/* Hover underline */}
                {!isActive && (
                  <span
                    className={`absolute -bottom-0.5 left-0 h-[2px] w-0 rounded-full transition-all duration-300 group-hover:w-full ${
                      lightSection ? "bg-[#008DB8]" : "bg-[#38BDF8]"
                    }`}
                  />
                )}
              </a>
            );
          })}
        </div>

        {/* Explore Platform — intentionally no navigation */}
        <motion.button
          type="button"
          whileHover={shouldReduceMotion ? undefined : { scale: 1.025, y: -1 }}
          whileTap={shouldReduceMotion ? undefined : { scale: 0.97 }}
          transition={{
            type: "spring",
            stiffness: 350,
            damping: 22,
          }}
          className={`group relative inline-flex shrink-0 items-center gap-3 overflow-hidden rounded-full border px-4 py-2.5 text-sm font-semibold shadow-lg backdrop-blur-md transition-all duration-300 sm:px-5 sm:py-3 ${
            lightSection
              ? "border-[#008DB8]/40 bg-white/80 text-[#142A36] hover:border-[#008DB8] hover:bg-[#00B8F0] hover:text-[#071C2B]"
              : "border-white/25 bg-white/[0.06] text-white hover:border-[#38BDF8] hover:bg-[#00B8F0] hover:text-[#071C2B]"
          }`}
        >
          {/* Hover sheen */}
          <span className="pointer-events-none absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/15 to-transparent transition-transform duration-700 group-hover:translate-x-full" />

          <span className="relative">Explore Platform</span>

          <span
            className={`relative flex h-7 w-7 items-center justify-center rounded-full transition-colors duration-300 ${
              lightSection
                ? "bg-[#008DB8]/10 group-hover:bg-[#071C2B]/10"
                : "bg-white/10 group-hover:bg-[#071C2B]/10"
            }`}
          >
            <ArrowRight
              size={16}
              className="transition-transform duration-300 group-hover:translate-x-1"
            />
          </span>
        </motion.button>
      </nav>
    </motion.header>
  );
}

export default Navbar;
