/**
 * @type {import('gatsby').GatsbyConfig}
 */
module.exports = {
  siteMetadata: {
    title: `My Gatsby Site`,
    siteUrl: `https://jackarnold84.github.io/cat5/`
  },
  pathPrefix: "/cat5",
  plugins: [
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