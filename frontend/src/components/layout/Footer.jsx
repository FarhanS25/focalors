function Footer() {
  return (
    <footer className="relative border-t border-white/15 bg-transparent text-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3 lg:px-10">
        <a href="#home" aria-label="FOCALORS home" className="shrink-0">
          <img
            src="/images/logo.png"
            alt="FOCALORS"
            className="w-28 object-contain"
          />
        </a>

        <p className="hidden text-xs text-white/80 sm:block">
          Hydraulic simulation. Smarter leak investigation.
        </p>

        <p className="text-xs text-white/75">
          © {new Date().getFullYear()} FOCALORS
        </p>
      </div>
    </footer>
  );
}

export default Footer;
