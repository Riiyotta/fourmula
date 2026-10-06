import Layout from '../layout/Layout.jsx'
import Hero from '../components/Hero.jsx'
import What from '../components/What.jsx'
import AiSection from '../components/AiSection.jsx'
import How from '../components/How.jsx'
import ListSection from '../components/ListSection.jsx'
import Faq from '../components/Faq.jsx'

export default function Home() {
  return (
    <Layout current="/" preloader>
      <Hero />
      <What />
      <AiSection />
      <How />
      <ListSection />
      <Faq />
    </Layout>
  )
}
