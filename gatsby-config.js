/**
 * @type {import('gatsby').GatsbyConfig}
 */
module.exports = {
  siteMetadata: {
    title: `My Gatsby Site`,
    siteUrl: `https://cat5.jarno.site`
  },
  plugins: [
    {
      resolve: 'gatsby-plugin-less',
      options: {
        lessOptions: {
          javascriptEnabled: true,
          modifyVars: {
            '@primary-color': '#c80f2d',
            '@font-size-base': '16px',
            '@font-family': "'Source Sans Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            '@border-radius-base': '8px',
            '@height-base': '44px',
            '@height-lg': '48px',
          },
        },
      },
    },
    "gatsby-plugin-styled-components",
    {
      resolve: `gatsby-plugin-manifest`,
      options: {
        name: "GatsbyJS",
        short_name: "GatsbyJS",
        start_url: "/",
        background_color: "#c80f2d",
        theme_color: "#c80f2d",
        display: "standalone",
        icon: "src/images/icon.png",
      },
    },
  ]
};