[10% off on all-access. Use codeSUPER10.\\
\\
Valid till \\
\\
0\\
\\
0123456789\\
\\
d : \\
\\
0\\
\\
0123456789\\
\\
0\\
\\
0123456789\\
\\
h :\\
\\
0\\
\\
0123456789\\
\\
0\\
\\
0123456789\\
\\
m :\\
\\
0\\
\\
0123456789\\
\\
0\\
\\
0123456789](https://ui.aceternity.com/pricing)

# Apple Cards Carousel

A sleek and minimal carousel implementation, as seen on apple.com

[card](https://ui.aceternity.com/categories/card) [features](https://ui.aceternity.com/categories/features) [carousel](https://ui.aceternity.com/categories/carousel)

PreviewCode

`npx shadcn@latest add @aceternity/apple-cards-carousel-demo`Copy

Copy prompt [Open in full screen](https://ui.aceternity.com/live-preview/apple-cards-carousel-demo) [Open in v0](https://v0.dev/chat/api/open?url=https://ui.aceternity.com/registry/apple-cards-carousel-demo.json)

## Get to know your iSad.

Artificial Intelligence

You can do more with AI.

![You can do more with AI.](https://images.unsplash.com/photo-1593508512255-86ab42a8e620?q=80&w=3556&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

Productivity

Enhance your productivity.

![Enhance your productivity.](https://images.unsplash.com/photo-1531554694128-c4c6665f59c2?q=80&w=3387&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

Product

Launching the new Apple Vision Pro.

![Launching the new Apple Vision Pro.](https://images.unsplash.com/photo-1713869791518-a770879e60dc?q=80&w=2333&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

Product

Maps for your iPhone 15 Pro Max.

![Maps for your iPhone 15 Pro Max.](https://images.unsplash.com/photo-1599202860130-f600f4948364?q=80&w=2515&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

iOS

Photography just got better.

![Photography just got better.](https://images.unsplash.com/photo-1602081957921-9137a5d6eaee?q=80&w=2793&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

Hiring

Hiring for a Staff Software Engineer

![Hiring for a Staff Software Engineer](https://images.unsplash.com/photo-1511984804822-e16ba72f5848?q=80&w=2048&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

## [Link to section](https://ui.aceternity.com/components/apple-cards-carousel\#installation) Installation

CLIManual

### Run the following command

```
npx shadcn@latest add @aceternity/apple-cards-carousel
Copy
```

### Add `useOutsideClick` hook

hooks/use-outside-click.ts

```
import React, { useEffect } from "react";

export const useOutsideClick = (
  ref: React.RefObject<HTMLDivElement>,
  callback: Function
) => {
  useEffect(() => {
    const listener = (event: any) => {
      if (!ref.current || ref.current.contains(event.target)) {
        return;
      }
      callback(event);
    };

    document.addEventListener("mousedown", listener);
    document.addEventListener("touchstart", listener);

    return () => {
      document.removeEventListener("mousedown", listener);
      document.removeEventListener("touchstart", listener);
    };
  }, [ref, callback]);
};CopySelect Language
```

## [Link to section](https://ui.aceternity.com/components/apple-cards-carousel\#examples) Examples

#### [Link to section](https://ui.aceternity.com/components/apple-cards-carousel\#standard) Standard

PreviewCode

`npx shadcn@latest add @aceternity/apple-cards-carousel-demo`Copy

Copy prompt [Open in full screen](https://ui.aceternity.com/live-preview/apple-cards-carousel-demo) [Open in v0](https://v0.dev/chat/api/open?url=https://ui.aceternity.com/registry/apple-cards-carousel-demo.json)

## Get to know your iSad.

Artificial Intelligence

You can do more with AI.

![You can do more with AI.](https://images.unsplash.com/photo-1593508512255-86ab42a8e620?q=80&w=3556&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

Productivity

Enhance your productivity.

![Enhance your productivity.](https://images.unsplash.com/photo-1531554694128-c4c6665f59c2?q=80&w=3387&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

Product

Launching the new Apple Vision Pro.

![Launching the new Apple Vision Pro.](https://images.unsplash.com/photo-1713869791518-a770879e60dc?q=80&w=2333&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

Product

Maps for your iPhone 15 Pro Max.

![Maps for your iPhone 15 Pro Max.](https://images.unsplash.com/photo-1599202860130-f600f4948364?q=80&w=2515&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

iOS

Photography just got better.

![Photography just got better.](https://images.unsplash.com/photo-1602081957921-9137a5d6eaee?q=80&w=2793&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

Hiring

Hiring for a Staff Software Engineer

![Hiring for a Staff Software Engineer](https://images.unsplash.com/photo-1511984804822-e16ba72f5848?q=80&w=2048&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

#### [Link to section](https://ui.aceternity.com/components/apple-cards-carousel\#with-layout-changes) With Layout Changes

PreviewCode

`npx shadcn@latest add @aceternity/apple-cards-carousel-demo-2`Copy

Copy prompt [Open in full screen](https://ui.aceternity.com/live-preview/apple-cards-carousel-demo-2) [Open in v0](https://v0.dev/chat/api/open?url=https://ui.aceternity.com/registry/apple-cards-carousel-demo-2.json)

## Get to know your iSad.

Artificial Intelligence

You can do more with AI.

![You can do more with AI.](https://images.unsplash.com/photo-1593508512255-86ab42a8e620?q=80&w=3556&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

Productivity

Enhance your productivity.

![Enhance your productivity.](https://images.unsplash.com/photo-1531554694128-c4c6665f59c2?q=80&w=3387&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

Product

Launching the new Apple Vision Pro.

![Launching the new Apple Vision Pro.](https://images.unsplash.com/photo-1713869791518-a770879e60dc?q=80&w=2333&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

Product

Maps for your iPhone 15 Pro Max.

![Maps for your iPhone 15 Pro Max.](https://images.unsplash.com/photo-1599202860130-f600f4948364?q=80&w=2515&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

iOS

Photography just got better.

![Photography just got better.](https://images.unsplash.com/photo-1602081957921-9137a5d6eaee?q=80&w=2793&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

Hiring

Hiring for a Staff Software Engineer

![Hiring for a Staff Software Engineer](https://images.unsplash.com/photo-1511984804822-e16ba72f5848?q=80&w=2048&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

## [Link to section](https://ui.aceternity.com/components/apple-cards-carousel\#props) Props

#### [Link to section](https://ui.aceternity.com/components/apple-cards-carousel\#carousel-component) Carousel Component

| Prop | Type | Default | Description |
| --- | --- | --- | --- |
| items | `JSX.Element[]` | Required | Array of JSX elements to be displayed in the carousel |
| initialScroll | `number` | 0 | Initial scroll position of the carousel |

#### [Link to section](https://ui.aceternity.com/components/apple-cards-carousel\#card-component) Card Component

| Prop | Type | Default | Description |
| --- | --- | --- | --- |
| card | `Card` | Required | Object containing card details (src, title, category, content) |
| index | `number` | Required | Index of the card in the carousel |
| layout | `boolean` | false | Whether to use layout animations |

#### [Link to section](https://ui.aceternity.com/components/apple-cards-carousel\#blurimage-component) BlurImage Component

| Prop | Type | Default | Description |
| --- | --- | --- | --- |
| height | `number | string` | - | Height of the image |
| width | `number | string` | - | Width of the image |
| src | `string` | Required | Source URL of the image |
| className | `string` | - | Additional CSS classes for the image |
| alt | `string` | "Background of a beautiful view" | Alt text for the image |
| ...rest | `ImageProps` | - | Any other props accepted by Next.js Image component |

Note: The `Card` type is defined as:

```
type Card = {
  src: string;
  title: string;
  category: string;
  content: React.ReactNode;
};CopySelect Language
```

## Build websites faster and 10x better than your competitors with  Aceternity UI Pro

Next.js 15, Tailwind CSS v4 and Motion for react powered templates

200+ templates and blocks combined

Ready to copy paste component blocks, save days of development time

[Get lifetime access](https://ui.aceternity.com/pricing) Talk to us

![Aceternity UI Pro Demo - Light Mode](https://assets.aceternity.com/cta-demo-light.webp)![Aceternity UI Pro Demo - Dark Mode](https://assets.aceternity.com/cta-demo-dark.webp)

[![Logo](https://ui.aceternity.com/logo.png)![Logo](https://ui.aceternity.com/logo-dark.png)\\
\\
Aceternity UI](https://ui.aceternity.com/)

Access an ever-growing collection of premium, meticulously crafted templates and Component Blocks.

A product by [Aceternity](https://www.aceternity.com/)

Building in public at [@mannupaaji](https://twitter.com/mannupaaji)

- Components
- [3D Card Effect](https://ui.aceternity.com/components/3d-card-effect)
- [3D Pin](https://ui.aceternity.com/components/3d-pin)
- [Animated Tooltip](https://ui.aceternity.com/components/animated-tooltip)
- [Aurora Background](https://ui.aceternity.com/components/aurora-background)
- [Background Beams](https://ui.aceternity.com/components/background-beams)
- [Bento Grid](https://ui.aceternity.com/components/bento-grid)
- [Card Hover Effect](https://ui.aceternity.com/components/card-hover-effect)
- [Floating Dock](https://ui.aceternity.com/components/floating-dock)
- [Globe](https://ui.aceternity.com/components/github-globe)
- [Hero Parallax](https://ui.aceternity.com/components/hero-parallax)
- [Infinite Moving Cards](https://ui.aceternity.com/components/infinite-moving-cards)
- [Lamp Effect](https://ui.aceternity.com/components/lamp-effect)
- [Macbook Scroll](https://ui.aceternity.com/components/macbook-scroll)
- [Moving Border](https://ui.aceternity.com/components/moving-border)
- [Parallax Scroll](https://ui.aceternity.com/components/parallax-scroll)
- [Sparkles](https://ui.aceternity.com/components/sparkles)
- [Text Generate Effect](https://ui.aceternity.com/components/text-generate-effect)
- [Timeline](https://ui.aceternity.com/components/timeline)
- [Tracing Beam](https://ui.aceternity.com/components/tracing-beam)
- [Wavy Background](https://ui.aceternity.com/components/wavy-background)

- Shadcn Compatible Blocks
- [Hero Sections](https://ui.aceternity.com/blocks/hero-sections)
- [Logo Clouds](https://ui.aceternity.com/blocks/logo-clouds)
- [Bento Grids](https://ui.aceternity.com/blocks/bento-grids)
- [CTA Sections](https://ui.aceternity.com/blocks/cta-sections)
- [Testimonials](https://ui.aceternity.com/blocks/testimonials)
- [Feature Sections](https://ui.aceternity.com/blocks/feature-sections)
- [Pricing Sections](https://ui.aceternity.com/blocks/pricing-sections)
- [Cards](https://ui.aceternity.com/blocks/cards)
- [Navbars](https://ui.aceternity.com/blocks/navbars)
- [Footers](https://ui.aceternity.com/blocks/footers)
- [Login and Signup](https://ui.aceternity.com/blocks/login-and-signup-sections)
- [Contact sections](https://ui.aceternity.com/blocks/contact-sections)
- [Blog Sections](https://ui.aceternity.com/blocks/blog-sections)
- [Blog Content Sections](https://ui.aceternity.com/blocks/blog-content-sections)
- [FAQs](https://ui.aceternity.com/blocks/faqs)
- [Sidebars](https://ui.aceternity.com/blocks/sidebars)
- [Stats Sections](https://ui.aceternity.com/blocks/stats-sections)
- [Backgrounds](https://ui.aceternity.com/blocks/backgrounds)

- Templates
- [Agenforce Marketing Template](https://ui.aceternity.com/templates/agenforce-marketing-template)
- [Nodus Marketing Template](https://ui.aceternity.com/templates/nodus-agent-template)
- [Startup Landing Page Template](https://ui.aceternity.com/templates/startup-landing-page-template)
- [AI SaaS Template](https://ui.aceternity.com/templates/ai-saas-template)
- [Proactiv Marketing Template](https://ui.aceternity.com/templates/proactiv-marketing-template)
- [Agenlabs Agency Template](https://ui.aceternity.com/templates/agenlabs-agency-template)
- [DevPro Portfolio Template](https://ui.aceternity.com/templates/devpro-portfolio-template)
- [Foxtrot Marketing Template](https://ui.aceternity.com/templates/foxtrot-marketing-template)
- [Playful Marketing Template](https://ui.aceternity.com/templates/playful-marketing-aceternity)
- [Cryptgen Marketing Template](https://ui.aceternity.com/templates/cryptgen-marketing-aceternity)
- [Schedule Marketing Template](https://ui.aceternity.com/templates/schedule-marketing-template)
- [Minimal Portfolio Template](https://ui.aceternity.com/templates/minimal-portfolio-template)

- Pages
- [Explore](https://ui.aceternity.com/explore)
- [Components](https://ui.aceternity.com/components)
- [Templates](https://ui.aceternity.com/templates)
- [Blocks](https://ui.aceternity.com/blocks)
- [Showcase](https://ui.aceternity.com/showcase)
- [Installation](https://ui.aceternity.com/installation)
- [Affiliate Program](https://ui.aceternity.com/affiliate-program)
- [Categories](https://ui.aceternity.com/categories)
- [Box Shadows](https://ui.aceternity.com/tools/box-shadows)
- [Pricing](https://ui.aceternity.com/pricing)
- [Changelog](https://ui.aceternity.com/changelog)
- [Pro](https://ui.aceternity.com/pro)
- [Aceternity UI](https://ui.aceternity.com/)
- [Aceternity Studio](https://www.aceternity.com/)
- [Licence](https://ui.aceternity.com/licence)
- [Refunds](https://ui.aceternity.com/refunds)
- [Privacy Policy](https://ui.aceternity.com/privacy)
- [Terms and Conditions](https://ui.aceternity.com/terms)
- [Twitter](https://x.com/aceternitylabs)
- [Discord](https://discord.gg/ftZbQvCdN7)
- [Brand Facts](https://ui.aceternity.com/brand-facts)
- [Guides](https://ui.aceternity.com/guides)

- Relevant
- [Best Modern Design Templates](https://ui.aceternity.com/best-modern-design-templates)
- [Best AI SaaS Templates](https://ui.aceternity.com/best-ai-saas-templates)
- [Best Marketing Templates](https://ui.aceternity.com/best-marketing-templates)
- [Best Minimal Templates in React and Next.js](https://ui.aceternity.com/best-minimal-templates-in-react-and-nextjs)
- [Best components and templates with Framer Motion](https://ui.aceternity.com/best-components-and-templates-with-framer-motion)
- [Amazing Tailwind CSS and Framer Motion Components](https://ui.aceternity.com/amazing-tailwindcss-and-framer-motion-components)
- [Best Shadcn Blocks and templates](https://ui.aceternity.com/shadcn-blocks)

© 2026 Aceternity Labs LLC. All Rights Reserved.

StripeM-Inner