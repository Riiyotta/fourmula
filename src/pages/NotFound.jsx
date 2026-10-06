import Layout from '../layout/Layout.jsx'
import NotFoundContent from './NotFoundContent.jsx'

// The original's 404 has no menu and no footer.
export default function NotFound() {
  return (
    <Layout current="/404" preloader menu={false} footer={false}>
      <NotFoundContent />
    </Layout>
  )
}
