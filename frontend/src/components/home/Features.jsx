import { motion, useReducedMotion } from "motion/react";
import { ArrowUpRight, MapPin, Activity, GitBranch } from "lucide-react";

const features = [
  {
    number: "01",
    icon: MapPin,
    title: "Start with the location.",
    emphasis: "Narrow the search.",
    description:
      "A citizen's reported location helps prioritize relevant areas of the water network and gives the investigation a meaningful starting point.",
    image: "/images/location-investigation.jpg",
    imageAlt: "Aerial view of an urban neighborhood and surrounding streets",
    label: "LOCATION & CONTEXT",
    category: "SPATIAL EVIDENCE",
  },
  {
    number: "02",
    icon: Activity,
    title: "Read the pressure.",
    emphasis: "Follow the evidence.",
    description:
      "Virtual pressure sensors provide hydraulic evidence that helps FOCALORS compare scenarios and rank possible leak locations.",
    image: "/images/pressure-analysis.jpg",
    imageAlt: "Water distribution pipes, valves, and pressure gauges",
    label: "HYDRAULIC ANALYSIS",
    category: "PRESSURE SIGNATURES",
  },
  {
    number: "03",
    icon: GitBranch,
    title: "Investigate further.",
    emphasis: "Measure with purpose.",
    description:
      "When several candidate pipes remain plausible, FOCALORS identifies a useful next measurement to help distinguish between them.",
    image: "/images/active-investigation.jpg",
    imageAlt: "Workers inspecting a water pipeline during a street excavation",
    label: "ACTIVE INVESTIGATION",
    category: "NEXT MEASUREMENT",
  },
];

const reveal = {
  hidden: {
    opacity: 0,
    y: 36,
    filter: "blur(5px)",
  },
  visible: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
  },
};

function Features() {
  const shouldReduceMotion = useReducedMotion();

  const revealTransition = {
    duration: shouldReduceMotion ? 0 : 0.75,
    ease: [0.22, 1, 0.36, 1],
  };

  const revealViewport = {
    once: true,
    amount: 0.15,
    margin: "0px 0px -60px 0px",
  };

  return (
    <section
      id="features"
      className="relative isolate overflow-hidden bg-transparent py-24 text-[var(--text)] sm:py-32"
    >
      {/* Subtle ambient background detail */}
      <motion.div
        aria-hidden="true"
        className="pointer-events-none absolute -right-40 top-0 -z-10 h-[500px] w-[500px] rounded-full bg-[color-mix(in_srgb,var(--teal)_8%,transparent)] blur-[130px]"
        animate={
          shouldReduceMotion
            ? undefined
            : {
                x: [0, -35, 0],
                y: [0, 30, 0],
                scale: [1, 1.08, 1],
              }
        }
        transition={{
          duration: 14,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      <div className="home-wrap">
        {/* Section heading */}
        <div className="grid gap-8 border-b border-white/15 pb-12 lg:grid-cols-[1.2fr_0.8fr] lg:items-end lg:pb-14">
          <motion.div
            variants={reveal}
            initial="hidden"
            whileInView="visible"
            viewport={revealViewport}
            transition={revealTransition}
          >
            <div className="mb-6 flex items-center gap-3">
              <motion.span
                className="h-[2px] w-9 bg-[var(--teal)]"
                initial={{ width: shouldReduceMotion ? 36 : 0 }}
                whileInView={{ width: 36 }}
                viewport={{ once: true }}
                transition={{ duration: 0.7, delay: 0.15 }}
              />

              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--teal)]">
                A different way to investigate
              </p>
            </div>

            <h2 className="home-section-title max-w-3xl">
              Complex networks.
              <span className="mt-2 block text-[var(--muted)]">
                Clearer decisions.
              </span>
            </h2>
          </motion.div>

          <motion.div
            className="max-w-md lg:justify-self-end"
            variants={reveal}
            initial="hidden"
            whileInView="visible"
            viewport={revealViewport}
            transition={{ ...revealTransition, delay: 0.15 }}
          >
            <p className="text-base leading-8 text-[var(--muted)]">
              Finding a possible leak is an investigation, not a guess. FOCALORS
              brings location information and hydraulic evidence together to
              guide the next step.
            </p>

            <div className="mt-6 flex items-center gap-3 text-xs font-medium uppercase tracking-[0.14em] text-[var(--muted)]">
              <motion.span
                className="h-2 w-2 rounded-full bg-[var(--teal)]"
                animate={
                  shouldReduceMotion
                    ? undefined
                    : {
                        opacity: [1, 0.45, 1],
                        scale: [1, 1.25, 1],
                      }
                }
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              />
              Three parts of the process
            </div>
          </motion.div>
        </div>

        {/* Asymmetrical feature layout */}
        <div className="grid gap-6 pt-10 lg:grid-cols-[1.12fr_0.88fr] lg:pt-12">
          {/* Main feature */}
          <motion.article
            className="group flex min-w-0 flex-col overflow-hidden"
            variants={reveal}
            initial="hidden"
            whileInView="visible"
            viewport={revealViewport}
            transition={revealTransition}
            whileHover={shouldReduceMotion ? undefined : { y: -5 }}
          >
            <div className="relative aspect-[5/3] overflow-hidden sm:aspect-[16/9]">
              <motion.img
                src={features[0].image}
                alt={features[0].imageAlt}
                loading="lazy"
                className="h-full w-full object-cover"
                initial={{
                  scale: shouldReduceMotion ? 1 : 1.12,
                }}
                whileInView={{ scale: 1 }}
                viewport={{ once: true }}
                transition={{
                  duration: shouldReduceMotion ? 0 : 1.2,
                  ease: [0.22, 1, 0.36, 1],
                }}
                whileHover={shouldReduceMotion ? undefined : { scale: 1.055 }}
              />

              <div className="absolute inset-0 bg-gradient-to-t from-[var(--bg)]/80 via-[var(--bg)]/10 to-transparent" />

              <div className="absolute left-5 top-5">
                <motion.span
                  className="inline-flex items-center gap-2 border border-white/20 bg-[var(--panel)] px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.13em] text-white backdrop-blur-sm"
                  initial={{ opacity: 0, x: -12 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.55, delay: 0.35 }}
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-[var(--teal)]" />
                  {features[0].label}
                </motion.span>
              </div>

              <motion.span
                className="absolute bottom-3 right-5 text-7xl font-light leading-none tracking-[-0.07em] text-white/90 sm:text-8xl"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.7, delay: 0.25 }}
              >
                01
              </motion.span>

              <div className="absolute bottom-5 left-5 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.15em] text-white/80">
                <span className="h-px w-7 bg-[var(--teal)]" />
                {features[0].category}
              </div>
            </div>

            <div className="flex flex-1 flex-col p-6 sm:p-9 lg:p-10">
              <div className="mb-8 flex items-center gap-3 border-b border-white/15 pb-5">
                <motion.div
                  whileHover={
                    shouldReduceMotion
                      ? undefined
                      : { rotate: -10, scale: 1.12 }
                  }
                  transition={{ type: "spring", stiffness: 300, damping: 15 }}
                >
                  <MapPin size={20} className="text-[var(--teal)]" />
                </motion.div>

                <span className="text-xs font-medium uppercase tracking-[0.14em] text-[var(--muted)]">
                  Feature / 01
                </span>
              </div>

              <h3 className="home-card-title">
                {features[0].title}
                <span className="mt-1 block text-[var(--muted)]">
                  {features[0].emphasis}
                </span>
              </h3>

              <p className="mt-5 max-w-lg text-sm leading-7 text-[var(--muted)] sm:text-base">
                {features[0].description}
              </p>

              <div className="mt-8 flex items-center gap-3 text-xs font-medium uppercase tracking-[0.13em] text-[var(--muted)]">
                <motion.span
                  className="h-[2px] bg-[var(--teal)]"
                  initial={{ width: shouldReduceMotion ? 32 : 0 }}
                  whileInView={{ width: 32 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.65, delay: 0.25 }}
                />
                The investigation starts here
              </div>
            </div>
          </motion.article>

          {/* Supporting features */}
          <div className="grid min-w-0 gap-6">
            {features.slice(1).map((feature, index) => {
              const Icon = feature.icon;

              return (
                <motion.article
                  key={feature.number}
                  className="group grid min-w-0 overflow-hidden sm:grid-cols-[0.8fr_1fr]"
                  variants={reveal}
                  initial="hidden"
                  whileInView="visible"
                  viewport={revealViewport}
                  transition={{
                    ...revealTransition,
                    delay: shouldReduceMotion ? 0 : 0.12 + index * 0.16,
                  }}
                  whileHover={shouldReduceMotion ? undefined : { y: -4, x: -2 }}
                >
                  <div className="relative min-h-56 overflow-hidden sm:min-h-full">
                    <motion.img
                      src={feature.image}
                      alt={feature.imageAlt}
                      loading="lazy"
                      className="absolute inset-0 h-full w-full object-cover"
                      initial={{
                        scale: shouldReduceMotion ? 1 : 1.1,
                      }}
                      whileInView={{ scale: 1 }}
                      viewport={{ once: true }}
                      transition={{
                        duration: shouldReduceMotion ? 0 : 1.1,
                        ease: [0.22, 1, 0.36, 1],
                      }}
                      whileHover={
                        shouldReduceMotion ? undefined : { scale: 1.06 }
                      }
                    />

                    <div className="absolute inset-0 bg-gradient-to-t from-[var(--bg)]/55 via-transparent to-transparent" />

                    <motion.span
                      className="absolute bottom-4 left-4 text-5xl font-light leading-none tracking-[-0.07em] text-white"
                      initial={{ opacity: 0, y: 14 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      viewport={{ once: true }}
                      transition={{
                        duration: 0.55,
                        delay: shouldReduceMotion ? 0 : 0.2,
                      }}
                    >
                      {feature.number}
                    </motion.span>
                  </div>

                  <div className="flex min-w-0 flex-col p-5 sm:p-6 lg:p-7">
                    <div className="flex items-center justify-between gap-3 border-b border-white/15 pb-4">
                      <span className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--muted)]">
                        {feature.label}
                      </span>

                      <motion.div
                        className="shrink-0 text-[var(--teal)]"
                        whileHover={
                          shouldReduceMotion
                            ? undefined
                            : {
                                rotate: [0, -8, 8, 0],
                                scale: 1.12,
                              }
                        }
                        transition={{
                          duration: 0.45,
                          ease: "easeInOut",
                        }}
                      >
                        <Icon size={19} strokeWidth={1.7} />
                      </motion.div>
                    </div>

                    <h3 className="mt-5 text-2xl font-semibold leading-tight tracking-[-0.04em]">
                      {feature.title}
                      <span className="mt-1 block text-[var(--muted)]">
                        {feature.emphasis}
                      </span>
                    </h3>

                    <p className="mt-4 flex-1 text-sm leading-7 text-[var(--muted)]">
                      {feature.description}
                    </p>

                    <div className="mt-6 border-t border-white/15 pt-4">
                      <span className="text-[10px] font-medium uppercase tracking-[0.12em] text-[var(--muted)]">
                        {feature.category}
                      </span>
                    </div>
                  </div>
                </motion.article>
              );
            })}
          </div>
        </div>

        {/* Closing statement */}
        <motion.div
          className="mt-12 flex flex-col gap-5 border-t border-white/15 pt-7 sm:flex-row sm:items-center sm:justify-between lg:mt-16"
          variants={reveal}
          initial="hidden"
          whileInView="visible"
          viewport={revealViewport}
          transition={{ ...revealTransition, delay: 0.1 }}
        >
          <p className="max-w-2xl text-sm leading-7 text-[var(--muted)]">
            Each measurement adds evidence. When uncertainty remains, the
            investigation continues with a more informed next step.
          </p>

          <motion.a
            href="#how-it-works"
            className="group inline-flex w-fit shrink-0 items-center gap-3 text-sm font-semibold text-white transition-colors hover:text-[var(--teal)]"
            whileHover={shouldReduceMotion ? undefined : { x: 4 }}
            whileTap={shouldReduceMotion ? undefined : { scale: 0.98 }}
          >
            Explore the process
            <motion.span
              className="flex h-10 w-10 items-center justify-center rounded-full border border-white/25 transition-colors group-hover:border-[var(--teal)]"
              whileHover={
                shouldReduceMotion
                  ? undefined
                  : {
                      borderColor: "#61e0bf",
                      rotate: 5,
                    }
              }
            >
              <ArrowUpRight
                size={18}
                className="transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5"
              />
            </motion.span>
          </motion.a>
        </motion.div>
      </div>
    </section>
  );
}

export default Features;
