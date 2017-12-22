const TelegramBot = require('node-telegram-bot-api')
const GitHubApi = require('github')
const github = new GitHubApi({
  debug: true
})

const token = 'TELE_TOKEN'
const bot = new TelegramBot(token, {polling: true})

bot.onText(/\/issue ([a-zA-Z0-9 ]+)-([a-zA-Z0-9 ]+)/, (msg, match) => {
	const chatId = msg.chat.id
	github.authenticate({
		type: 'token',
		token: 'GIT_TOKEN'
	})
	github.issues.create({
		owner: 'ORG',
		repo: 'REPO',
		title: match[1],
		body: match[2]
	})
	bot.sendMessage(chatId, 'Successfully add ' + match[1])
})

bot.hears('hi', (ctx) =>('Hello, ctx.message.new_chat_member

console.log('Running! use [ctrl] + [c] to stop services.')
