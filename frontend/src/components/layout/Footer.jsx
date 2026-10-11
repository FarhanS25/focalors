import { Droplets } from "lucide-react";

function Footer() {
  return (
    <footer>
      <div className="home-wrap home-footer">
        <a href="#home" aria-label="FOCALORS home" className="home-brand">
          <span className="home-mark" aria-hidden="true">
            <Droplets size={18} />
          </span>
          <span>
            <b>FOCALORS</b>
          </span>
        </a>

        <p>Hydraulic simulation. Smarter leak investigation.</p>

        <p>© {new Date().getFullYear()} FOCALORS</p>
      </div>
    </footer>
  );
}

export default Footer;
