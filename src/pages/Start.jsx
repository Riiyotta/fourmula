import Layout from '../layout/Layout.jsx'

/**
 * Local stand-in for app.fourmula.ai/start.
 *
 * The real target is a Next.js app that ships an empty shell
 * (BAILOUT_TO_CLIENT_SIDE_RENDERING) -- there is no server-rendered markup to
 * transcribe, so this is NOT a replica of that app. It is a page composed from
 * this project's own design system (the `.tech` inner-page layout, the `u-*`
 * type scale, `btn-primary` / `btn-outline`) so the clone stays self-contained
 * and the CTAs lead somewhere that looks like it belongs.
 */
export default function Start() {
  return (
    <Layout current="/start">
      <section className="tech">
        <h1 className="tech__title u-h3 u-fonts-100">
          Get started
          <br />
          <span className="u-fonts-50">with Fourmula</span>
        </h1>
        <div className="tech__rich u-fonts-100 w-richtext">
          <p className="u-body-1 u-fonts-64">
            This is a local placeholder for the product onboarding flow. The live
            application renders entirely client-side, so no markup was available to
            reproduce here.
          </p>
          <div
            style={{
              display: 'flex',
              gap: '0.75rem',
              flexWrap: 'wrap',
              marginTop: '2rem',
            }}
          >
            <a href="/auth" className="btn-primary u-btn w-inline-block">
              <div>Sign in</div>
            </a>
            <a href="/" className="btn-outline u-btn w-inline-block">
              <div>Back to site</div>
            </a>
          </div>
        </div>
      </section>
    </Layout>
  )
}
