<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  select: [emoji: string]
  close: []
}>()

const emojiCategories = [
  {
    name: '表情',
    emojis: ['😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '😊', '😇', '', '😍', '🤩', '😘', '😗', '😚', '😙', '😋', '😛', '😜', '🤪', '', '🤑', '', '🤭', '', '🤔', '', '🤨', '😐', '😑', '😶', '🫥', '😏', '😒', '🙄', '😬', '🤥', '😌', '😔', '😪', '🤤', '😴', '😷', '🤒', '🤕', '', '🤮', '🥵', '🥶', '🥴', '😵', '🤯', '🤠', '🥳', '🥸', '😎', '🤓', '🧐']
  },
  {
    name: '手势',
    emojis: ['👋', '🤚', '🖐️', '', '🖖', '🫱', '🫲', '🫳', '', '👌', '🤌', '🤏', '✌️', '🤞', '🫰', '', '🤘', '', '👈', '👉', '👆', '🖕', '', '☝️', '🫵', '👍', '👎', '✊', '👊', '', '🤜', '👏', '🙌', '🫶', '', '🤲', '🤝', '🙏']
  },
  {
    name: '动物',
    emojis: ['', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '', '🐻‍❄️', '🐨', '🐯', '🦁', '🐮', '', '🐸', '', '🙈', '🙉', '🙊', '🐧', '', '🐤', '🐣', '🦆', '🦅', '🦉', '🦇', '', '🐗', '', '🦄', '🐝', '🪱', '🐞']
  },
  {
    name: '食物',
    emojis: ['', '🍐', '', '🍋', '', '🍉', '🍇', '🍓', '🫐', '🍈', '🍒', '', '🥭', '🍍', '🥥', '🥝', '🍅', '🍆', '', '🥦', '🥬', '🥒', '🌶️', '🫑', '🌽', '🥕', '🫒', '', '🧅', '', '🍠', '🥐', '🥯', '🍞', '🥖', '🥨', '🧀', '🥚', '', '🧇', '', '🥩', '', '🌭', '🍔', '🍟', '🍕', '🫓', '🥪', '', '🧆', '🌮', '🌯', '🫔', '', '🥘', '', '🥫', '', '🍜', '🍲', '🍛', '🍣', '🍱', '🥟', '🦪', '🍤', '', '🍚', '', '🍥', '🥠', '🥮', '🍢', '', '🍧', '🍨', '🍦', '🥧', '', '🍰', '🎂', '🍮', '🍭', '', '🍫', '', '🍩', '', '🌰', '', '🍯', '🥛', '🍼', '☕', '', '🧃', '🧋', '🍶', '🍺', '🍻', '🥂', '🍷', '🥃', '', '🍹', '', '🫗']
  },
  {
    name: '爱心',
    emojis: ['❤️', '🧡', '', '💚', '💙', '', '🖤', '🤍', '🤎', '💔', '❣️', '💕', '💞', '', '💗', '💖', '', '💝', '💟', '♥️', '🫶', '', '😘', '💋', '‍❤️‍👨', '👨‍❤️‍', '👩‍❤️‍👩', '💑', '👩‍❤️‍💋‍', '👨‍❤️‍💋‍👨', '‍❤️‍💋‍']
  },
  {
    name: '物品',
    emojis: ['⌚', '📱', '📲', '💻', '⌨️', '🖥️', '🖨️', '🖱️', '🖲️', '', '💾', '💿', '', '📼', '📷', '📸', '📹', '🎥', '📽️', '️', '📞', '☎️', '📟', '📠', '📺', '📻', '️', '🎚️', '️', '🧭', '️', '⏲️', '', '🕰️', '', '⏳', '', '🔌', '💡', '🔦', '🕯️', '🪔', '🛢️', '', '💴', '💶', '', '🪙', '💰', '💳', '💎', '⚖️', '🪜', '🧰', '🪛', '🔧', '', '⚒️', '️', '⛏️', '', '🔩', '⚙️', '🪤', '🧲', '⛓️', '🔫', '💣', '🧨', '🪓', '🔪', '🗡️', '⚔️', '🛡️', '🚬', '⚰️', '🪦', '⚱️', '🏺', '🔮', '', '🧿', '', '💈', '⚗️', '🔭', '', '🕳️', '', '🩺', '🩻', '💊', '💉', '', '🧬', '🦠', '🧫', '🧪', '🌡️', '🪠', '', '🧻', '🚽', '🚰', '🚿', '🛁', '🛀', '', '🪒', '🧽', '🧴', '🛎️', '🔑', '🗝️', '🚪', '🪑', '️', '🛏️', '', '🧸', '🪆', '🖼️', '🪞', '🪟', '🛍️', '🛒', '🎁', '', '🎏', '', '🪄', '🪅', '🎊', '🎉', '', '🏮', '', '✉️', '📩', '📨', '📧', '', '📥', '📤', '📦', '🏷️', '🪧', '📪', '', '📬', '📭', '📮', '📯', '', '📃', '📄', '📑', '🧾', '📊', '📈', '', '🗒️', '️', '📆', '', '🗑️', '📇', '🗃️', '🗳️', '🗄️', '📋', '📁', '📂', '️', '🗞️', '', '📓', '📔', '📕', '📗', '📘', '📙', '📚', '📖', '🔖', '🧷', '🔗', '', '🖇️', '', '📏', '🧮', '📌', '📍', '✂️', '🖊️', '🖋️', '✒️', '🖌️', '🖍️', '📝', '✏️', '', '🔎', '🔏', '🔐', '🔒', '🔓']
  }
]

const activeCategory = ref(0)
const recentEmojis = ref<string[]>([])

const selectEmoji = (emoji: string) => {
  emit('select', emoji)
  if (!recentEmojis.value.includes(emoji)) {
    recentEmojis.value.unshift(emoji)
    if (recentEmojis.value.length > 20) {
      recentEmojis.value.pop()
    }
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="emoji-modal">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-end justify-center">
        <div class="absolute inset-0 bg-black/30" @click="emit('close')"></div>
        
        <div class="relative w-full max-w-lg bg-surface-container-low rounded-t-3xl overflow-hidden animate-slide-up">
          <div class="p-4 pb-6">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-title-sm text-title-sm text-on-surface">表情</h3>
              <button @click="emit('close')" class="p-2 rounded-full hover:bg-surface-container-high transition-colors">
                <span class="material-symbols-outlined text-on-surface-variant">close</span>
              </button>
            </div>

            <div v-if="recentEmojis.length > 0" class="mb-4">
              <p class="text-xs text-on-surface-variant mb-2 font-label-bold">最近使用</p>
              <div class="flex flex-wrap gap-1">
                <button 
                  v-for="emoji in recentEmojis" 
                  :key="emoji"
                  @click="selectEmoji(emoji)"
                  class="w-10 h-10 flex items-center justify-center text-xl hover:bg-surface-container-high rounded-lg transition-colors active:scale-90"
                >
                  {{ emoji }}
                </button>
              </div>
            </div>

            <div class="flex gap-2 overflow-x-auto no-scrollbar mb-4 pb-2">
              <button 
                v-for="(cat, index) in emojiCategories" 
                :key="cat.name"
                @click="activeCategory = index"
                class="px-3 py-1.5 rounded-full text-xs font-label-bold whitespace-nowrap transition-colors flex-shrink-0"
                :class="activeCategory === index ? 'bg-primary text-white' : 'bg-surface-container-high text-on-surface-variant hover:bg-surface-container'"
              >
                {{ cat.name }}
              </button>
            </div>

            <div class="grid grid-cols-8 gap-1 max-h-64 overflow-y-auto no-scrollbar">
              <button 
                v-for="emoji in emojiCategories[activeCategory].emojis.filter(e => e.trim() !== '')" 
                :key="emoji"
                @click="selectEmoji(emoji)"
                class="w-10 h-10 flex items-center justify-center text-xl hover:bg-surface-container-high rounded-lg transition-colors active:scale-90"
              >
                {{ emoji }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
@keyframes slide-up {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}

.animate-slide-up {
  animation: slide-up 0.3s ease-out;
}

.emoji-modal-enter-active,
.emoji-modal-leave-active {
  transition: opacity 0.3s ease;
}

.emoji-modal-enter-from,
.emoji-modal-leave-to {
  opacity: 0;
}
</style>
