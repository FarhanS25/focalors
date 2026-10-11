import { motion, useReducedMotion } from "motion/react";
import { Droplets, Network, Target } from "lucide-react";

const principles = [
  {
    icon: Network,
    title: "Network-aware",
    description:
      "Use hydraulic network structure and pressure measurements to narrow down potential leak locations.",
  },
  {
    icon: Target,
    title: "Evidence-driven",
    description:
      "Rank candidate pipes by how closely simulated pressure signatures match the observed measurements.",
  },
  {
    icon: Droplets,
    title: "Measurement-efficient",
    description:
      "Identify useful next measurements when the available evidence is not enough to distinguish candidates.",
  },
];

const reveal = {
  hidden: {
    opacity: 0,
    y: 28,
    filter: "blur(4px)",
  },
  visible: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
  },
};

function Mission() {
  const shouldReduceMotion = useReducedMotion();

  const transition = {
    duration: shouldReduceMotion ? 0 : 0.75,
    ease: [0.22, 1, 0.36, 1],
  };

  const viewport = {
    once: true,
    amount: 0.15,
  };

  return (
    <section
      id="mission"
      className="relative isolate overflow-hidden bg-transparent py-24 sm:py-32"
    >
      {/* Background image with restrained cinematic movement */}
      <div className="pointer-events-none absolute inset-0 -z-20 overflow-hidden">
        <motion.img
          src="/images/mission.jpg"
          alt=""
          aria-hidden="true"
          className="h-full w-full object-cover object-center"
          loading="lazy"
          initial={{
            scale: shouldReduceMotion ? 1 : 1.08,
          }}
          whileInView={{ scale: 1 }}
          viewport={{ once: true }}
          transition={{
            duration: shouldReduceMotion ? 0 : 1.8,
            ease: [0.22, 1, 0.36, 1],
          }}
        />
      </div>

      {/* Minimal gradient behind text only */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-gradient-to-r from-black/50 via-black/15 to-transparent" />

      <div className="mx-auto max-w-7xl px-6 lg:px-10">
        <div className="grid items-center gap-14 lg:grid-cols-[1.05fr_0.95fr] lg:gap-20">
          {/* Main content */}
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={viewport}
            variants={{
              hidden: {},
              visible: {
                transition: {
                  staggerChildren: shouldReduceMotion ? 0 : 0.14,
                },
              },
            }}
          >
            <motion.div
              className="mb-6 inline-flex items-center gap-3"
              variants={reveal}
              transition={transition}
            >
              <motion.span
                className="h-px bg-[#00B8F0]"
                initial={{ width: shouldReduceMotion ? 40 : 0 }}
                whileInView={{ width: 40 }}
                viewport={{ once: true }}
                transition={{ duration: 0.7, delay: 0.15 }}
              />

              <span className="text-xs font-bold uppercase tracking-[0.24em] text-[#38BDF8]">
                Why FOCALORS
              </span>
            </motion.div>

            <motion.h2
              className="max-w-2xl text-4xl font-semibold leading-[1.12] tracking-tight text-white sm:text-5xl lg:text-6xl"
              variants={reveal}
              transition={transition}
            >
              Finding the signal
              <span className="block text-[#38BDF8]">beneath the surface.</span>
            </motion.h2>

            <motion.p
              className="mt-7 max-w-xl text-base leading-8 text-white sm:text-lg"
              variants={reveal}
              transition={transition}
            >
              Water leaks can be difficult to localize when pressure
              measurements are sparse and many pipes remain plausible
              candidates. FOCALORS explores how hydraulic simulation and
              systematic measurement selection can make that investigation more
              focused.
            </motion.p>

            <motion.p
              className="mt-5 max-w-xl text-base leading-8 text-white/90"
              variants={reveal}
              transition={transition}
            >
              By comparing simulated pressure signatures and updating candidate
              rankings as new measurements become available, the system aims to
              reduce uncertainty rather than rely on a single guess.
            </motion.p>
          </motion.div>

          {/* Principles */}
          <div className="relative">
            {/* Corner accents */}
            <motion.div
              aria-hidden="true"
              className="absolute -left-3 -top-3 h-16 w-16 border-l border-t border-[#38BDF8]/70"
              initial={{
                opacity: 0,
                x: -8,
                y: -8,
              }}
              whileInView={{
                opacity: 1,
                x: 0,
                y: 0,
              }}
              viewport={{ once: true }}
              transition={transition}
            />

            <motion.div
              aria-hidden="true"
              className="absolute -bottom-3 -right-3 h-16 w-16 border-b border-r border-[#38BDF8]/70"
              initial={{
                opacity: 0,
                x: 8,
                y: 8,
              }}
              whileInView={{
                opacity: 1,
                x: 0,
                y: 0,
              }}
              viewport={{ once: true }}
              transition={{ ...transition, delay: 0.2 }}
            />

            <motion.div
              className="relative space-y-4"
              initial="hidden"
              whileInView="visible"
              viewport={viewport}
              variants={{
                hidden: {},
                visible: {
                  transition: {
                    staggerChildren: shouldReduceMotion ? 0 : 0.16,
                    delayChildren: shouldReduceMotion ? 0 : 0.1,
                  },
                },
              }}
            >
              {principles.map((principle, index) => {
                const Icon = principle.icon;

                return (
                  <motion.article
                    key={principle.title}
                    variants={reveal}
                    transition={transition}
                    whileHover={
                      shouldReduceMotion
                        ? undefined
                        : {
                            x: -4,
                            borderColor: "rgba(56, 189, 248, 0.65)",
                            backgroundColor: "rgba(0, 0, 0, 0.36)",
                          }
                    }
                    className="group flex gap-5 rounded-xl border border-white/25 bg-black/25 p-5 backdrop-blur-sm transition-colors duration-300 hover:border-[#38BDF8]/50 hover:bg-black/35 sm:p-6"
                  >
                    {/* Icon container */}
                    <motion.div
                      className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-[#38BDF8]/40 bg-black/25 text-[#38BDF8] transition-colors duration-300 group-hover:bg-black/40"
                      whileHover={
                        shouldReduceMotion
                          ? undefined
                          : {
                              scale: 1.08,
                              rotate: -4,
                            }
                      }
                      transition={{
                        type: "spring",
                        stiffness: 300,
                        damping: 18,
                      }}
                    >
                      <Icon size={22} strokeWidth={1.7} />
                    </motion.div>

                    <div className="flex-1">
                      <div className="mb-2 flex items-center gap-3">
                        <h3 className="font-semibold text-white sm:text-lg">
                          {principle.title}
                        </h3>

                        <motion.span
                          className="text-xs font-medium tracking-widest text-[#7DD3FC]"
                          initial={{ opacity: 0 }}
                          whileInView={{ opacity: 1 }}
                          viewport={{ once: true }}
                          transition={{
                            duration: 0.5,
                            delay: shouldReduceMotion ? 0 : 0.2 + index * 0.1,
                          }}
                        >
                          0{index + 1}
                        </motion.span>
                      </div>

                      <p className="text-sm leading-7 text-white/85">
                        {principle.description}
                      </p>
                    </div>
                  </motion.article>
                );
              })}
            </motion.div>
          </div>
        </div>

        {/* Bottom accent */}
        <motion.div
          className="mt-20 flex items-center gap-4 border-t border-white/30 pt-6"
          variants={reveal}
          initial="hidden"
          whileInView="visible"
          viewport={viewport}
          transition={{ ...transition, delay: 0.1 }}
        >
          <motion.div
            className="shrink-0 text-[#38BDF8]"
            animate={
              shouldReduceMotion
                ? undefined
                : {
                    y: [0, -3, 0],
                  }
            }
            transition={{
              duration: 2.5,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            <Droplets size={18} />
          </motion.div>

          <p className="text-xs font-medium uppercase tracking-[0.18em] text-white/85">
            Hydraulic simulation · Pressure analysis · Active investigation
          </p>
        </motion.div>
      </div>
    </section>
  );
}

export default Mission;
