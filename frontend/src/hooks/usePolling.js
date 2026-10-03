import { useEffect, useRef } from 'react'
import { getDebateStatus } from '../api/debate'
import useDebateStore from '../store/debateStore'

export default function usePolling(debateId, active) {
  const intervalRef = useRef(null)
  const updateStatus = useDebateStore((s) => s.updateStatus)

  useEffect(() => {
    if (!debateId || !active) return

    const poll = async () => {
      try {
        const { data } = await getDebateStatus(debateId)
        updateStatus(data)
        if (data.status === 'completed') {
          clearInterval(intervalRef.current)
        }
      } catch (e) {
        console.error('Polling error:', e)
      }
    }

    poll()
    intervalRef.current = setInterval(poll, 3000)
    return () => clearInterval(intervalRef.current)
  }, [debateId, active])
}