import { create } from 'zustand'

const useDebateStore = create((set, get) => ({
  debateId: null,
  topic: '',
  status: null,
  phase: null,
  messages: [],
  roundNumber: 0,
  timeElapsed: 0,
  timeBudget: 0,
  confidenceHistory: [],
  userBet: null,

  setDebate: (id, topic, timeBudget) =>
    set({ debateId: id, topic, timeBudget, status: 'in_progress', messages: [], phase: 'initialization' }),

  setUserBet: (bet) => set({ userBet: bet }),

  updateStatus: (data) => {
    const { messages, confidenceHistory } = get()
    const newMessages = [...messages]

    if (data.latest_event && data.latest_event.event_type !== 'debate_started') {
      const last = messages[messages.length - 1]
      const isDuplicate = last &&
        last.agent === data.latest_event.agent &&
        last.event_type === data.latest_event.event_type &&
        last.timestamp === data.latest_event.timestamp
      if (!isDuplicate) {
        newMessages.push(data.latest_event)
      }
    }

    const newConfidence = [...confidenceHistory]
    if (data.phase === 'rebuttal_rounds' && data.latest_event?.event_type === 'round_evaluation') {
      newConfidence.push({
        round: data.current_round_number,
        score: 0.5,
      })
    }

    set({
      status: data.status,
      phase: data.phase,
      roundNumber: data.current_round_number,
      timeElapsed: data.time_elapsed,
      timeBudget: data.time_budget,
      messages: newMessages,
      confidenceHistory: newConfidence,
    })
  },

  reset: () => set({
    debateId: null, topic: '', status: null, phase: null,
    messages: [], roundNumber: 0, timeElapsed: 0, timeBudget: 0,
    confidenceHistory: [], userBet: null,
  }),
}))

export default useDebateStore