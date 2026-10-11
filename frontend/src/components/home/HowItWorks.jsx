import { motion, useReducedMotion } from "motion/react";
import {
  ArrowDownRight,
  MapPin,
  Activity,
  GitBranch,
  Search,
} from "lucide-react";

const steps = [
  {
    number: "01",
    icon: MapPin,
    title: "Report a concern",
    description:
      "A citizen reports a suspected leak location, giving the investigation a useful starting point.",
    tag: "LOCATION INPUT",
  },
  {
    number: "02",
    icon: Search,
    title: "Build a spatial prior",
    description:
      "The reported location helps prioritize relevant areas of the simulated water network.",
    tag: "NARROW THE SEARCH",
  },
  {
    number: "03",
    icon: Activity,
    title: "Analyze pressure readings",
    description:
      "Virtual sensors provide pressure measurements that can be compared against candidate leak scenarios.",
    tag: "HYDRAULIC EVIDENCE",
  },
  {
    number: "04",
    icon: GitBranch,
    title: "Rank candidate pipes",
    description:
      "The engine compares simulated and observed pressure signatures to rank possible pipe locations.",
    tag: "CANDIDATE RANKING",
  },
  {
    number: "05",
    icon: ArrowDownRight,
    title: "Choose the next measurement",
    description:
      "If the result remains ambiguous, the engine can select a useful next measurement to help distinguish candidates.",
    tag: "ACTIVE INVESTIGATION",
  },
];

const reveal = {
  hidden: {
    opacity: 0,
    y: 30,
    filter: "blur(4px)",
  },
  visible: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
  },
};

function HowItWorks() {
  const shouldReduceMotion = useReducedMotion();

  const transition = {
    duration: shouldReduceMotion ? 0 : 0.7,
    ease: [0.22, 1, 0.36, 1],
  };

  const viewport = {
    once: true,
    amount: 0.15,
    margin: "0px 0px -50px 0px",
  };

  return (
    <section
      id="how-it-works"
      className="relative overflow-hidden bg-[#E8EEF1] py-24 text-[#142A36] sm:py-32"
    >
      {/* Animated background accent */}
      <motion.div
        aria-hidden="true"
        className="pointer-events-none absolute -left-48 top-20 h-[420px] w-[420px] rounded-full bg-sky-300/20 blur-[120px]"
        animate={
          shouldReduceMotion
            ? undefined
            : {
                x: [0, 35, 0],
                y: [0, 25, 0],
                scale: [1, 1.08, 1],
              }
        }
        transition={{
          duration: 16,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      <div className="relative mx-auto max-w-7xl px-6 lg:px-10">
        {/* Section heading */}
        <div className="grid gap-8 border-b border-[#C8D5DC] pb-12 lg:grid-cols-[1.2fr_0.8fr] lg:items-end lg:pb-14">
          <motion.div
            variants={reveal}
            initial="hidden"
            whileInView="visible"
            viewport={viewport}
            transition={transition}
          >
            <div className="mb-6 flex items-center gap-3">
              <motion.span
                className="h-[2px] bg-[#00B8F0]"
                initial={{ width: shouldReduceMotion ? 36 : 0 }}
                whileInView={{ width: 36 }}
                viewport={{ once: true }}
                transition={{ duration: 0.65, delay: 0.15 }}
              />

              <p className="text-xs font-semibold uppercase tracking-[0.23em] text-[#327B99]">
                The investigation process
              </p>
            </div>

            <h2 className="max-w-2xl text-4xl font-semibold leading-[1.08] tracking-[-0.045em] sm:text-5xl lg:text-6xl">
              From a reported concern
              <span className="mt-2 block text-[#708B9B]">
                to a clearer picture.
              </span>
            </h2>
          </motion.div>

          <motion.div
            className="max-w-lg lg:justify-self-end"
            variants={reveal}
            initial="hidden"
            whileInView="visible"
            viewport={viewport}
            transition={{ ...transition, delay: 0.15 }}
          >
            <p className="text-base leading-8 text-[#526A78]">
              FOCALORS combines location information with pressure measurements
              to narrow down possible leak locations. When the evidence is
              ambiguous, it helps identify the next useful measurement.
            </p>

            <div className="mt-6 flex items-center gap-3 text-xs font-semibold uppercase tracking-[0.13em] text-[#526A78]">
              <motion.span
                className="h-2 w-2 rounded-full bg-[#00B8F0]"
                animate={
                  shouldReduceMotion
                    ? undefined
                    : {
                        opacity: [1, 0.45, 1],
                        scale: [1, 1.2, 1],
                      }
                }
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              />
              Five steps · Evidence-led analysis
            </div>
          </motion.div>
        </div>

        {/* Main content */}
        <div className="mt-12 grid gap-12 lg:grid-cols-[1fr_0.92fr] lg:gap-16">
          {/* Animated timeline */}
          <div className="relative">
            {/* Timeline track */}
            <div
              aria-hidden="true"
              className="absolute bottom-10 left-[23px] top-10 w-px bg-[#C4D4DC]"
            />

            {/* Timeline progress */}
            <motion.div
              aria-hidden="true"
              className="absolute left-[22.5px] top-10 w-[2px] origin-top bg-[#00B8F0]"
              initial={{ scaleY: shouldReduceMotion ? 1 : 0 }}
              whileInView={{ scaleY: 1 }}
              viewport={{ once: true, amount: 0.1 }}
              transition={{
                duration: shouldReduceMotion ? 0 : 1.8,
                ease: [0.22, 1, 0.36, 1],
                delay: 0.2,
              }}
              style={{ height: "calc(100% - 5rem)" }}
            />

            <div className="space-y-3">
              {steps.map((step, index) => {
                const Icon = step.icon;

                return (
                  <motion.article
                    key={step.number}
                    className="group relative grid grid-cols-[48px_1fr] gap-4 py-4 sm:grid-cols-[48px_1fr] sm:gap-5"
                    variants={reveal}
                    initial="hidden"
                    whileInView="visible"
                    viewport={viewport}
                    transition={{
                      ...transition,
                      delay: shouldReduceMotion ? 0 : index * 0.12,
                    }}
                  >
                    {/* Step marker */}
                    <motion.div
                      className="relative z-10 flex h-12 w-12 items-center justify-center rounded-full border border-[#B8D5E2] bg-[#E8EEF1] transition-colors duration-300 group-hover:border-[#00B8F0] group-hover:bg-[#D7EDF5]"
                      whileHover={
                        shouldReduceMotion
                          ? undefined
                          : {
                              scale: 1.1,
                              borderColor: "#00B8F0",
                            }
                      }
                      whileTap={
                        shouldReduceMotion ? undefined : { scale: 0.96 }
                      }
                      transition={{
                        type: "spring",
                        stiffness: 320,
                        damping: 18,
                      }}
                    >
                      <motion.div
                        className="text-[#2587AA] transition-colors group-hover:text-[#087EA4]"
                        whileHover={
                          shouldReduceMotion ? undefined : { rotate: -8 }
                        }
                        transition={{ duration: 0.25 }}
                      >
                        <Icon size={19} strokeWidth={1.7} />
                      </motion.div>
                    </motion.div>

                    {/* Step information */}
                    <div className="min-w-0 border-b border-[#CFDCE2] pb-6">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-[#568095]">
                          STEP {step.number}
                        </span>

                        <span className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#77909D]">
                          {step.tag}
                        </span>
                      </div>

                      <h3 className="mt-3 text-lg font-semibold tracking-tight text-[#142A36] transition-colors duration-300 group-hover:text-[#087EA4] sm:text-xl">
                        {step.title}
                      </h3>

                      <p className="mt-2 max-w-lg text-sm leading-7 text-[#526A78]">
                        {step.description}
                      </p>
                    </div>
                  </motion.article>
                );
              })}
            </div>
          </div>

          {/* Image and supporting information */}
          <motion.div
            className="lg:pt-6"
            variants={reveal}
            initial="hidden"
            whileInView="visible"
            viewport={viewport}
            transition={{ ...transition, delay: 0.15 }}
          >
            {/* Feature image */}
            <motion.div
              className="group relative overflow-hidden rounded-2xl bg-[#172B36] shadow-2xl shadow-[#142A36]/10"
              whileHover={shouldReduceMotion ? undefined : { y: -4 }}
              transition={{
                type: "spring",
                stiffness: 220,
                damping: 24,
              }}
            >
              <motion.img
                src="/images/leak.png"
                alt="Water escaping from a damaged urban water pipe"
                loading="lazy"
                className="h-[380px] w-full object-cover sm:h-[500px]"
                initial={{
                  scale: shouldReduceMotion ? 1 : 1.12,
                }}
                whileInView={{ scale: 1 }}
                viewport={{ once: true }}
                transition={{
                  duration: shouldReduceMotion ? 0 : 1.2,
                  ease: [0.22, 1, 0.36, 1],
                }}
                whileHover={shouldReduceMotion ? undefined : { scale: 1.045 }}
              />

              <div className="absolute inset-0 bg-gradient-to-t from-[#10232E]/95 via-[#10232E]/20 to-transparent" />

              {/* Image label */}
              <motion.div
                className="absolute left-5 top-5 sm:left-7 sm:top-7"
                initial={{ opacity: 0, x: -12 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: 0.3 }}
              >
                <span className="inline-flex items-center gap-2 border border-white/20 bg-[#172B36]/75 px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-white backdrop-blur-md">
                  <motion.span
                    className="h-1.5 w-1.5 rounded-full bg-[#00B8F0]"
                    animate={
                      shouldReduceMotion ? undefined : { opacity: [1, 0.45, 1] }
                    }
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: "easeInOut",
                    }}
                  />
                  Network investigation
                </span>
              </motion.div>

              {/* Image caption */}
              <div className="absolute inset-x-0 bottom-0 p-6 sm:p-8">
                <motion.div
                  initial={{ opacity: 0, y: 18 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.65, delay: 0.25 }}
                >
                  <span className="mb-4 block text-xs font-semibold uppercase tracking-[0.17em] text-sky-300">
                    Evidence before assumptions
                  </span>

                  <h3 className="max-w-md text-3xl font-semibold leading-tight tracking-[-0.035em] text-white sm:text-4xl">
                    Better measurements.
                    <span className="mt-1 block text-[#9FB8C6]">
                      More informed decisions.
                    </span>
                  </h3>

                  <p className="mt-4 max-w-md text-sm leading-7 text-white/75">
                    Compare candidate rankings, examine pressure data, and
                    identify where another measurement could provide useful
                    evidence.
                  </p>
                </motion.div>
              </div>
            </motion.div>

            {/* Supporting strip */}
            <motion.div
              className="mt-5 grid grid-cols-2 border-y border-[#C8D5DC] py-5"
              variants={reveal}
              initial="hidden"
              whileInView="visible"
              viewport={viewport}
              transition={{ ...transition, delay: 0.2 }}
            >
              <div className="pr-4">
                <span className="block text-[10px] font-semibold uppercase tracking-[0.14em] text-[#668291]">
                  Investigation basis
                </span>

                <p className="mt-2 text-sm font-medium text-[#203D4B]">
                  Simulated hydraulic evidence
                </p>
              </div>

              <div className="border-l border-[#C8D5DC] pl-5">
                <span className="block text-[10px] font-semibold uppercase tracking-[0.14em] text-[#668291]">
                  Decision approach
                </span>

                <p className="mt-2 text-sm font-medium text-[#203D4B]">
                  Evidence-led prioritization
                </p>
              </div>
            </motion.div>

            {/* CTA */}
            <motion.a
              href="#mission"
              className="group mt-6 inline-flex items-center gap-3 text-sm font-semibold text-[#183644] transition-colors hover:text-[#087EA4]"
              whileHover={shouldReduceMotion ? undefined : { x: 4 }}
              whileTap={shouldReduceMotion ? undefined : { scale: 0.98 }}
            >
              Explore the investigation platform
              <motion.span
                className="flex h-9 w-9 items-center justify-center rounded-full border border-[#B8CBD4] transition-colors group-hover:border-[#00B8F0] group-hover:bg-[#D7EDF5]"
                whileHover={
                  shouldReduceMotion
                    ? undefined
                    : {
                        rotate: 5,
                        borderColor: "#00B8F0",
                      }
                }
                transition={{ duration: 0.25 }}
              >
                <ArrowDownRight
                  size={17}
                  className="transition-transform group-hover:translate-x-0.5 group-hover:translate-y-0.5"
                />
              </motion.span>
            </motion.a>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

export default HowItWorks;
