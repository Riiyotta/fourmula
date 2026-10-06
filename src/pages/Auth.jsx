import Layout from '../layout/Layout.jsx'

/**
 * Local stand-in for app.fourmula.ai/auth.
 *
 * The real target renders entirely client-side and sits behind sign-in, so there
 * was no markup to transcribe -- this is NOT a replica of that screen. It is
 * composed from this project's own design system purely so the two "Sign in"
 * links resolve inside the clone instead of leaving for an external domain.
 *
 * The form is deliberately INERT: no `action`, no submit handler, no state, no
 * network call, and nothing is read from or stored for the fields. It exists as
 * layout only. Do not wire it up to anything.
 */
export default function Auth() {
  return (
    <Layout current="/auth">
      <section className="tech">
        <h1 className="tech__title u-h3 u-fonts-100">
          Sign in
          <br />
          <span className="u-fonts-50">to continue</span>
        </h1>
        <div className="tech__rich u-fonts-100 w-richtext">
          <p className="u-body-1 u-fonts-64">
            Layout placeholder only &mdash; this form is inert and submits nowhere.
          </p>
          <form
            onSubmit={(e) => e.preventDefault()}
            style={{ maxWidth: '22rem', marginTop: '2rem' }}
            aria-label="Inert placeholder form"
          >
            <label className="u-title-2 u-fonts-50" htmlFor="auth-email">
              Email
            </label>
            <input
              id="auth-email"
              type="text"
              className="w-input"
              placeholder="you@company.com"
              style={{ marginTop: '.5rem', marginBottom: '1rem' }}
            />
            <button type="submit" className="btn-primary u-btn" style={{ width: '100%' }}>
              Continue
            </button>
          </form>
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '2rem' }}>
            <a href="/" className="btn-outline u-btn w-inline-block">
              <div>Back to site</div>
            </a>
          </div>
        </div>
      </section>
    </Layout>
  )
}
