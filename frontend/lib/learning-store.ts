/**
 * Shared learning progress store (Phase 3) — XP, completed modules, quiz
 * answers. Persisted in localStorage under one key so /learn and the
 * category quizzes share the same progress.
 */

export const LEARNING_KEY = "eco-nojin-learning-progress";

export interface LearningState {
  xp: number;
  completed: string[];
  answered: string[]; // quiz question ids already answered (no repeat XP)
}

export const XP_PER_LEVEL = 100;

export function levelFor(xp: number): number {
  return Math.floor(xp / XP_PER_LEVEL) + 1;
}

export function loadLearning(): LearningState {
  if (typeof window === "undefined") {
    return { xp: 0, completed: [], answered: [] };
  }
  try {
    const raw = localStorage.getItem(LEARNING_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<LearningState>;
      return {
        xp: parsed.xp ?? 0,
        completed: parsed.completed ?? [],
        answered: parsed.answered ?? [],
      };
    }
  } catch {
    /* corrupt storage -> fresh state */
  }
  return { xp: 0, completed: [], answered: [] };
}

export function saveLearning(state: LearningState): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(LEARNING_KEY, JSON.stringify(state));
  } catch {
    /* storage full/blocked -> in-memory only */
  }
}

/** Mark a module complete; returns true when it was newly completed. */
export function completeModule(state: LearningState, moduleId: string, xp: number): LearningState {
  if (state.completed.includes(moduleId)) return state;
  return {
    ...state,
    xp: state.xp + xp,
    completed: [...state.completed, moduleId],
  };
}

/** Record a correct quiz answer; returns the new state + awarded XP. */
export function answerQuizQuestion(
  state: LearningState,
  questionId: string,
  xpReward: number
): { state: LearningState; awarded: number } {
  if (state.answered.includes(questionId)) {
    return { state, awarded: 0 };
  }
  return {
    state: { ...state, xp: state.xp + xpReward, answered: [...state.answered, questionId] },
    awarded: xpReward,
  };
}
