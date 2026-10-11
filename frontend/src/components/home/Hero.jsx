import {
  motion,
  useReducedMotion,
  useScroll,
  useTransform,
} from "motion/react";
import { useRef } from "react";
import { ArrowRight, Activity, ShieldCheck, Waves } from "lucide-react";

function Hero() {
  const shouldReduceMotion = useReducedMotion();
  const heroRef = useRef(null);

  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  });

  const backgroundY = useTransform(
    scrollYProgress,
    [0, 1],
    ["0%", shouldReduceMotion ? "0%" : "18%"],
  );

  const backgroundScale = useTransform(
    scrollYProgress,
    [0, 1],
    [1.05, shouldReduceMotion ? 1.05 : 1.15],
  );

  const entrance = {
    hidden: {
      opacity: 0,
      y: shouldReduceMotion ? 0 : 32,
      filter: shouldReduceMotion ? "blur(0px)" : "blur(8px)",
    },
    visible: {
      opacity: 1,
      y: 0,
      filter: "blur(0px)",
      transition: {
        duration: shouldReduceMotion ? 0 : 0.9,
        ease: [0.22, 1, 0.36, 1],
      },
    },
  };

  const sequence = {
    hidden: {},
    visible: {
      transition: {
        staggerChildren: shouldReduceMotion ? 0 : 0.16,
        delayChildren: shouldReduceMotion ? 0 : 0.2,
      },
    },
  };

  return (
    <section
      id="home"
      ref={heroRef}
      className="relative flex min-h-screen items-center overflow-hidden bg-[#071C2B]"
    >
      {/* Cinematic background with scroll-linked movement */}
      <motion.div
        className="absolute inset-0"
        style={
          shouldReduceMotion
            ? undefined
            : {
                y: backgroundY,
                scale: backgroundScale,
              }
        }
      >
        <motion.img
          src="/images/hero.png"
          alt="Aerial view of a river flowing through a city"
          initial={shouldReduceMotion ? false : { scale: 1.16, opacity: 0.6 }}
          animate={{ scale: 1.05, opacity: 1 }}
          transition={{
            duration: shouldReduceMotion ? 0 : 2.4,
            ease: [0.16, 1, 0.3, 1],
          }}
          className="h-full w-full object-cover"
        />
      </motion.div>

      {/* Cinematic contrast */}
      <div className="absolute inset-0 bg-gradient-to-r from-[#04111B]/85 via-[#071C2B]/45 to-[#071C2B]/10" />
      <div className="absolute inset-0 bg-gradient-to-t from-[#071C2B]/80 via-transparent to-[#071C2B]/20" />

      {/* Atmospheric light */}
      <motion.div
        aria-hidden="true"
        className="pointer-events-none absolute -right-40 top-1/4 h-[480px] w-[480px] rounded-full bg-sky-400/[0.08] blur-[120px]"
        animate={
          shouldReduceMotion
            ? undefined
            : {
                x: [0, -35, 0],
                y: [0, 25, 0],
                scale: [1, 1.12, 1],
              }
        }
        transition={{
          duration: 12,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      {/* Fine animated light line */}
      <motion.div
        aria-hidden="true"
        className="pointer-events-none absolute left-0 top-[30%] h-px w-1/2 origin-left bg-gradient-to-r from-transparent via-sky-300/50 to-transparent"
        initial={{ scaleX: 0, opacity: 0 }}
        animate={{ scaleX: 1, opacity: 1 }}
        transition={{
          duration: shouldReduceMotion ? 0 : 1.8,
          delay: shouldReduceMotion ? 0 : 1,
          ease: [0.22, 1, 0.36, 1],
        }}
      />

      <div className="relative z-10 mx-auto w-full max-w-7xl px-6 pb-24 pt-32 lg:px-10">
        <motion.div
          variants={sequence}
          initial="hidden"
          animate="visible"
          className="max-w-4xl"
        >
          {/* Status label */}
          <motion.div
            variants={entrance}
            className="mb-9 inline-flex items-center gap-3 rounded-full border border-white/20 bg-[#071C2B]/35 px-4 py-2.5 backdrop-blur-xl"
          >
            <span className="relative flex h-2.5 w-2.5">
              <motion.span
                className="absolute inset-0 rounded-full bg-sky-400"
                animate={
                  shouldReduceMotion
                    ? undefined
                    : {
                        scale: [1, 2.1, 1],
                        opacity: [0.8, 0, 0.8],
                      }
                }
                transition={{
                  duration: 2.2,
                  repeat: Infinity,
                  ease: "easeOut",
                }}
              />
              <span className="relative h-2.5 w-2.5 rounded-full bg-sky-400 shadow-[0_0_12px_rgba(56,189,248,0.8)]" />
            </span>

            <span className="text-[10px] font-semibold uppercase tracking-[0.22em] text-white/90 sm:text-xs">
              Intelligent Water Network Investigation
            </span>

            <Waves size={14} className="text-sky-300" />
          </motion.div>

          {/* Headline */}
          <div className="overflow-hidden">
            <motion.h1
              variants={entrance}
              className="text-5xl font-semibold leading-[1.06] tracking-[-0.045em] text-white sm:text-6xl lg:text-8xl"
            >
              Every drop
              <br />
              tells a story.
            </motion.h1>
          </div>

          <div className="mt-1 overflow-hidden">
            <motion.div variants={entrance}>
              <span className="block text-5xl font-semibold leading-[1.1] tracking-[-0.045em] text-sky-400 sm:text-6xl lg:text-8xl">
                Find the leak.
              </span>
            </motion.div>
          </div>

          {/* Accent rule */}
          <motion.div
            variants={entrance}
            className="mt-7 flex items-center gap-3"
          >
            <motion.span
              className="h-[2px] bg-sky-400"
              initial={{ width: 0 }}
              animate={{ width: 56 }}
              transition={{
                duration: shouldReduceMotion ? 0 : 0.8,
                delay: shouldReduceMotion ? 0 : 0.9,
              }}
            />
            <span className="text-[10px] font-medium uppercase tracking-[0.24em] text-white/55">
              From pressure data to informed decisions
            </span>
          </motion.div>

          {/* Description */}
          <motion.p
            variants={entrance}
            className="mt-7 max-w-xl text-base leading-8 text-white/80 sm:text-lg"
          >
            Water leaks don't always reveal themselves. FOCALORS combines
            citizen reports and pressure measurements to investigate water
            networks and identify the pipes most worth examining.
          </motion.p>

          {/* Actions */}
          <motion.div
            variants={entrance}
            className="mt-10 flex flex-col gap-4 sm:flex-row"
          >
            <motion.a
              href="#mission"
              whileHover={shouldReduceMotion ? undefined : { y: -3 }}
              whileTap={shouldReduceMotion ? undefined : { scale: 0.98 }}
              className="group relative inline-flex items-center justify-center gap-3 overflow-hidden rounded-full bg-sky-400 px-7 py-4 text-sm font-semibold text-[#071C2B] transition-colors hover:bg-sky-300"
            >
              <motion.span
                aria-hidden="true"
                className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/35 to-transparent"
                whileHover={
                  shouldReduceMotion ? undefined : { x: ["0%", "250%"] }
                }
                transition={{ duration: 0.7 }}
              />
              <span className="relative">Explore the Platform</span>
              <ArrowRight
                size={18}
                className="relative transition-transform duration-300 group-hover:translate-x-1"
              />
            </motion.a>

            <motion.a
              href="#how-it-works"
              whileHover={shouldReduceMotion ? undefined : { y: -3 }}
              whileTap={shouldReduceMotion ? undefined : { scale: 0.98 }}
              className="inline-flex items-center justify-center gap-3 rounded-full border border-white/30 bg-white/[0.06] px-7 py-4 text-sm font-medium text-white backdrop-blur-md transition-colors hover:border-white/60 hover:bg-white/10"
            >
              Discover How It Works
              <span className="text-sky-300">↘</span>
            </motion.a>
          </motion.div>

          {/* Feature highlights */}
          <motion.div
            variants={sequence}
            className="mt-16 grid max-w-2xl grid-cols-1 gap-6 border-t border-white/20 pt-7 sm:grid-cols-2"
          >
            <motion.div
              variants={entrance}
              whileHover={shouldReduceMotion ? undefined : { x: 5 }}
              className="group flex items-start gap-4"
            >
              <div className="rounded-xl border border-white/15 bg-white/[0.08] p-3 transition-colors duration-300 group-hover:border-sky-400/40 group-hover:bg-sky-400/10">
                <Activity className="text-sky-400" size={22} />
              </div>

              <div>
                <h3 className="text-sm font-semibold text-white">
                  Pressure-driven analysis
                </h3>
                <p className="mt-1 text-sm leading-6 text-white/65">
                  Compare simulated sensor readings across the network.
                </p>
              </div>
            </motion.div>

            <motion.div
              variants={entrance}
              whileHover={shouldReduceMotion ? undefined : { x: 5 }}
              className="group flex items-start gap-4"
            >
              <div className="rounded-xl border border-white/15 bg-white/[0.08] p-3 transition-colors duration-300 group-hover:border-sky-400/40 group-hover:bg-sky-400/10">
                <ShieldCheck className="text-sky-400" size={22} />
              </div>

              <div>
                <h3 className="text-sm font-semibold text-white">
                  Guided investigation
                </h3>
                <p className="mt-1 text-sm leading-6 text-white/65">
                  Rank candidate pipes and guide the next measurement.
                </p>
              </div>
            </motion.div>
          </motion.div>
        </motion.div>
      </div>

      {/* Process indicator */}
      <motion.div
        initial={{ opacity: 0, x: 25 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{
          duration: shouldReduceMotion ? 0 : 0.8,
          delay: shouldReduceMotion ? 0 : 1.6,
        }}
        className="absolute bottom-8 right-6 hidden items-center gap-4 text-[10px] uppercase tracking-[0.2em] text-white/60 md:flex lg:right-10"
      >
        <span>Observe</span>
        <span className="h-px w-8 bg-white/40" />
        <span>Investigate</span>
        <span className="h-px w-8 bg-white/40" />
        <span>Understand</span>
      </motion.div>

      {/* Scroll cue */}
      <motion.div
        aria-hidden="true"
        className="absolute bottom-8 left-1/2 hidden -translate-x-1/2 flex-col items-center gap-2 text-white/45 md:flex"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: shouldReduceMotion ? 0 : 1.8 }}
      >
        <span className="text-[9px] uppercase tracking-[0.25em]">
          Scroll to explore
        </span>

        <motion.span
          className="h-8 w-px origin-top bg-gradient-to-b from-sky-400 to-transparent"
          animate={shouldReduceMotion ? undefined : { scaleY: [1, 0.55, 1] }}
          transition={{
            duration: 1.8,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </motion.div>
    </section>
  );
}

export default Hero;
