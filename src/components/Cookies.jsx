export default function Cookies() {
  return (
    <>
      <section className="cookies">
      <div fs-cc="banner" className="cookies__modal__wrap" style={{ display: "flex" }}>
      <div className="cookies__modal__main">
      <a fs-cc="close" href="/#" className="cookies__modal__close w-inline-block" role="button" tabIndex="0">
      <div className="cookies__modal__close-icon w-embed">
      <svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="none"><path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeLinejoin="round"></path></svg></div>
      <div className="u-hidden-copy">Close cookies modal</div></a>
      <div className="cookies__modal__copy">
      <div className="cookies__modal__title u-title-3 u-fonts-100">Cookie settings</div>
      <div className="cookies__modal__text u-title-2 u-fonts-50">By clicking "Accept all cookies", you agree to storing cookies on your device to enhance site navigation, analyze site usage and assist in our marketing efforts as outlined in our <a href="/#" className="fs-cc_link">privacy policy</a>.</div></div>
      <div className="fs-cc_modal-buttons">
      <a fs-cc="allow" href="/#" className="btn-primary u-btn is-cookies w-inline-block" role="button" tabIndex="0">
      <div>Accept all</div></a>
      <a fs-cc="open-preferences" href="/#" className="btn-outline u-btn is-cookies w-inline-block" role="button" tabIndex="0">
      <div>Settings</div></a></div></div></div>
      <div fs-cc="preferences" className="cookies__list__wrap" style={{ display: "none" }}>
      <div className="cookie-preference_wrapper">
      <div className="fs-cc_modal">
      <a fs-cc="close" href="/#" className="cookies__modal__close w-inline-block" role="button" tabIndex="0">
      <div className="fs-cc_screen-reader-only">Close Cookie Preference Manager</div>
      <div className="cookies__modal__close-icon w-embed">
      <svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="none"><path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeLinejoin="round"></path></svg></div></a>
      <div className="cookies__modal__copy">
      <div className="cookies__modal__title u-title-3 u-fonts-100">Cookie settings</div>
      <div className="cookies__modal__text u-title-2 u-fonts-50">By clicking "Accept all cookies", you agree to storing cookies on your device to enhance site navigation, analyze site usage and assist in our marketing efforts as outlined in our <a href="/#" className="fs-cc_link">privacy policy</a>.</div>
      <div className="fs-cc_form w-form w-form-loading">
      <form id="ck-form" name="wf-form-ck-form" data-name="ck-form" method="get" className="fs-cc_preferences" data-wf-page-id="6936c73e0da5b3bc5bb89cbf" data-wf-element-id="ddf5bbb2-dfdc-14cd-6d57-cf04c257a300" data-turnstile-sitekey="0x4AAAAAAAQTptj2So4dx43e" aria-label="ck-form">
      <div className="fs-cc_checkbox is--not-allowed w-clearfix">
      <div className="fs-cc_checkbox-button _w--redirected-checked"></div>
      <div className="fs-cc_titles u-title-1">Strictly necessary (always active)</div>
      <div className="cookies__modal__text u-title-2 u-fonts-50">Cookies required to enable basic website functionality.</div></div><label className="w-checkbox fs-cc_checkbox w-clearfix">
      <div className="w-checkbox-input w-checkbox-input--inputType-custom fs-cc_checkbox-button"></div>
      <input type="checkbox" name="Fs-Marketing" id="fs__marketing" data-name="Fs Marketing" fs-cc-checkbox="marketing" style={{ position: "absolute", zIndex: "-1" }} />
      <span htmlFor="Fs-Marketing" className="fs-cc_titles u-title-1 w-form-label">Marketing</span>
      <div className="cookies__modal__text u-title-2 u-fonts-50 is-02">Cookies used to deliver advertising that is more relevant to you and your interests.</div></label><label className="w-checkbox fs-cc_checkbox w-clearfix">
      <div className="w-checkbox-input w-checkbox-input--inputType-custom fs-cc_checkbox-button"></div>
      <input type="checkbox" name="Fs-Personalization" id="fs__personalization" data-name="Fs Personalization" fs-cc-checkbox="personalization" style={{ position: "absolute", zIndex: "-1" }} />
      <span htmlFor="Fs-Personalization" className="fs-cc_titles u-title-1 w-form-label">Personalization<br /></span>
      <div className="cookies__modal__text u-title-2 u-fonts-50 is-03">Cookies allowing the website to remember choices you make (such as your user name, language, or the region you are in).</div></label><label className="w-checkbox fs-cc_checkbox w-clearfix">
      <div className="w-checkbox-input w-checkbox-input--inputType-custom fs-cc_checkbox-button"></div>
      <input type="checkbox" name="Fs-Analytics" id="fs__analytics" data-name="Fs Analytics" fs-cc-checkbox="analytics" style={{ position: "absolute", zIndex: "-1" }} />
      <span htmlFor="Fs-Analytics" className="fs-cc_titles u-title-1 w-form-label">Analytics<br /></span>
      <div className="cookies__modal__text u-title-2 u-fonts-50 is-04">Cookies helping understand how this website performs, how visitors interact with the site, and whether there may be technical issues.</div></label></form>
      <div className="fs-cc_modal-buttons is-form">
      <a fs-cc="allow" href="/#" className="btn-primary u-btn is-cookies w-inline-block" role="button" tabIndex="0">
      <div>Accept all</div></a>
      <a fs-cc="submit" href="/#" className="btn-outline u-btn is-cookies w-inline-block" role="button" tabIndex="0">
      <div>Save changes</div></a></div>
      <div className="hide-all w-form-done" tabIndex="-1" role="region" aria-label="ck-form success"></div>
      <div className="hide-all w-form-fail" tabIndex="-1" role="region" aria-label="ck-form failure"></div></div></div></div></div>
      <div fs-cc="close" className="cookie-preference_background"></div></div></section>
    </>
  )
}
