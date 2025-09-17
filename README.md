# 2024 SIH Backend

Basic TypeScript + Express server scaffold.

## Scripts

- `npm run dev` – Start development server with Nodemon + ts-node.
- `npm run build` – Compile TypeScript to `dist`.
- `npm start` – Run compiled JavaScript from `dist`.
- `npm run clean` – Remove `dist` folder.

## Getting Started

```bash
npm install
npm run dev
```

Visit: http://localhost:3000/

## Environment Variables

Create a `.env` file if needed:

```
PORT=4000
```

## Production Build

```bash
npm run build
npm start
```

## Project Structure

```
src/
  index.ts        # Express app entry
```

Generated `dist/` contains compiled JS after build.

## Next Steps

- Add routes/controllers
- Add logging (e.g. morgan / pino)
- Add error handling middleware
- Add tests (Jest / Vitest)
