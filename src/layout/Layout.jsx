import { useEffect } from 'react'
import loadSite from '../loadSite.js'

import Preloader from '../components/Preloader.jsx'
import Cookies from '../components/Cookies.jsx'
import Header from '../components/Header.jsx'
import Menu from '../components/Menu.jsx'
import Footer from '../components/Footer.jsx'
import AwwwardsBadge from '../components/AwwwardsBadge.jsx'

/**
 * Global chrome, composed exactly as the original does per page:
 *
 *   route              preloader  menu  footer  badge
 *   /                  yes        yes   yes     yes
 *   /privacy-policy    no         yes   yes     yes
 *   /terms-of-service  no         yes   yes     yes
 *   404                yes        no    no      yes
 *
 * The original is a real multi-page site, so navigation is plain <a> full page
 * loads. The router only picks which page renders for the current URL, which
 * keeps the markup identical and lets the preloader re-run per navigation as
 * it does on the original.
 */
export default function Layout({
  current = '/',
  preloader = false,
  menu = true,
  footer = true,
  children,
}) {
  useEffect(() => {
    loadSite()
  }, [])

  return (
    <>
      {preloader && <Preloader />}
      <Cookies />
      <section className="page">
        <Header current={current} />
        {menu && <Menu current={current} />}
        {children}
        {footer && <Footer current={current} />}
      </section>
      <AwwwardsBadge />
    </>
  )
}
