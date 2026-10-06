export default function Menu({ current = "/" }) {
  const cur = (h) => (current === h ? { "aria-current": "page" } : {})
  const act = (h, base) => base + (current === h ? " w--current" : "")
  return (
    <>
      <section className="menu">
      <div className="menu__wrap-main">
      <div className="menu__wrap" style={{ overflow: "hidden", padding: "0rem", height: "2.7rem", width: "15rem" }}>
      <div className="menu__item">
      <div className="menu__label u-small-text-1 u-fonts-50">Menu</div>
      <div className="menu__list">
      <a hover-stagger="" href="/#pdp" className="menu__link u-title-3 u-fonts-100">
      PDP's</a>
      <a hover-stagger="" href="/#products" className="menu__link u-title-3 u-fonts-100">
      Products</a>
      <a hover-stagger="" href="/#video" className="menu__link u-title-3 u-fonts-100">
      Videos</a>
      <a hover-stagger="" href="/#list" className="menu__link u-title-3 u-fonts-100">
      Our features</a></div></div>
      <div className="menu__item is-lined">
      <div className="menu__label u-small-text-1 u-fonts-50">Other</div>
      <div className="menu__list">
      <a hover-stagger="" href="/privacy-policy" {...cur("/privacy-policy")} className={act("/privacy-policy", "menu__link u-title-2 u-fonts-100")}>
      Privacy Policy</a>
      <a hover-stagger="" href="/terms-of-service" {...cur("/terms-of-service")} className={act("/terms-of-service", "menu__link u-title-2 u-fonts-100")}>
      Terms of Service</a>
      <a hover-stagger="" href="/#" className="menu__link u-title-2 u-fonts-100">
      Cookie Policy</a></div></div>
      <div className="menu__item is-last">
      <div className="menu__label u-small-text-1 u-fonts-50">Social media</div>
      <div className="menu__list is-row">
      <a hover-stagger="" href="#" className="menu__link u-title-2 u-fonts-100">
      Instagram</a>
      <a hover-stagger="" href="/#" className="menu__link u-title-2 u-fonts-100 is-hide">
      Linkedin</a>
      <a href="/#" hover-stagger="" className="menu__link u-title-2 u-fonts-100 is-hide">
      Youtube</a></div></div>
      <div className="menu__item is-auth">
      <a hover-stagger-wrap="" href="/start" className="btn-primary u-btn is-menu w-inline-block">
      <div hover-stagger="">
      Ge tstarted</div></a>
      <a href="/auth" className="header_signin w-inline-block">
      <div className="header_signin-icon w-embed">
      <svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 16 16" fill="none"><path d="M8.00065 1.33301C6.25398 1.33301 4.83398 2.75301 4.83398 4.49967C4.83398 6.21301 6.17398 7.59967 7.92065 7.65967C7.97398 7.65301 8.02732 7.65301 8.06732 7.65967C8.08065 7.65967 8.08732 7.65967 8.10065 7.65967C8.10732 7.65967 8.10732 7.65967 8.11398 7.65967C9.82065 7.59967 11.1607 6.21301 11.1673 4.49967C11.1673 2.75301 9.74732 1.33301 8.00065 1.33301Z" fill="currentColor"></path><path d="M11.3866 9.43293C9.52664 8.19293 6.49331 8.19293 4.61997 9.43293C3.77331 9.9996 3.30664 10.7663 3.30664 11.5863C3.30664 12.4063 3.77331 13.1663 4.61331 13.7263C5.54664 14.3529 6.77331 14.6663 7.99997 14.6663C9.22664 14.6663 10.4533 14.3529 11.3866 13.7263C12.2266 13.1596 12.6933 12.3996 12.6933 11.5729C12.6866 10.7529 12.2266 9.99293 11.3866 9.43293Z" fill="currentColor"></path></svg></div>
      <div className="u-hidden-copy">Fourmula app account</div></a></div></div></div></section>
    </>
  )
}
