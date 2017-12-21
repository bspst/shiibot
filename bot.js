const Telegraf = require('telegraf')


const bot = new Telegraf(process.env.TOKEN)
bot.start((ctx) => {
  console.log('started:', ctx.from.id)
  return ctx.reply('Welcome!')
})
bot.hears('hi', (ctx) => ctx.reply('Hey!'))
bot.hears('hello', (ctx) => ctx.reply('Futari Saison, Boku Wa Iya Da!'))

bot.startPolling()
