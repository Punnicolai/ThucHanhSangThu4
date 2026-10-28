const pagesUrl = process.env.CI_PAGES_URL;
const target = pagesUrl ? new URL(pagesUrl) : null;
module.exports = {
  title: 'Lab 06 - DevSecOps',
  tagline: 'Thực hành CI/CD với GitLab',
  url: target ? target.origin : 'http://localhost:3000',
  baseUrl: target ? `${target.pathname.replace(/\/$/, '')}/` : '/',
  onBrokenLinks: 'throw',
  i18n: {defaultLocale: 'vi', locales: ['vi']},
  presets: [['classic', {
    docs: {routeBasePath: '/', sidebarPath: require.resolve('./sidebars.js')},
    blog: false,
    theme: {customCss: require.resolve('./src/css/custom.css')}
  }]],
  themeConfig: {
    navbar: {title: 'LAB 06', items: [{to: '/', label: 'Bài thực hành', position: 'left'}]},
    footer: {style: 'dark', copyright: 'Lab 06 - Bảo mật với DevSecOps'}
  }
};
