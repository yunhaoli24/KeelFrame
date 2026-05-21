<script setup lang="ts">
import { toTypedSchema } from "@vee-validate/zod";
import { useForm } from "vee-validate";
import { z } from "zod";

import { FormField } from "@/components/ui/form";

import type { DictType, DictTypePayload } from "@/services/api/system/dict/dict-types.api";

const props = defineProps<{
  dictType: DictType | null;
  loading?: boolean;
}>();

const emits = defineEmits<{
  (e: "submit", payload: DictTypePayload): void;
}>();

const formSchema = toTypedSchema(
  z.object({
    name: z.string().trim().min(1, "Please enter a name."),
    code: z.string().trim().min(1, "Please enter a code."),
    remark: z.string().optional(),
  }),
);

function getInitialValues(dictType: DictType | null) {
  return {
    name: dictType?.name ?? "",
    code: dictType?.code ?? "",
    remark: dictType?.remark ?? "",
  };
}

const { handleSubmit, resetForm } = useForm({
  validationSchema: formSchema,
  initialValues: getInitialValues(props.dictType),
});

watch(
  () => props.dictType,
  (dictType) => {
    resetForm({ values: getInitialValues(dictType) });
  },
  { immediate: true },
);

const onSubmit = handleSubmit((values) => {
  const payload: DictTypePayload = {
    name: values.name.trim(),
    code: values.code.trim(),
    remark: values.remark?.trim() ? values.remark.trim() : null,
  };

  emits("submit", payload);
});
</script>

<template>
  <form class="space-y-6" @submit="onSubmit">
    <FormField v-slot="{ componentField }" name="name">
      <UiFormItem>
        <UiFormLabel>Name</UiFormLabel>
        <UiFormControl>
          <UiInput v-bind="componentField" placeholder="Dict type name" :disabled="loading" />
        </UiFormControl>
        <UiFormMessage />
      </UiFormItem>
    </FormField>

    <FormField v-slot="{ componentField }" name="code">
      <UiFormItem>
        <UiFormLabel>Code</UiFormLabel>
        <UiFormControl>
          <UiInput v-bind="componentField" placeholder="dict_type_code" :disabled="loading" />
        </UiFormControl>
        <UiFormMessage />
      </UiFormItem>
    </FormField>

    <FormField v-slot="{ componentField }" name="remark">
      <UiFormItem>
        <UiFormLabel>Remark</UiFormLabel>
        <UiFormControl>
          <UiTextarea v-bind="componentField" placeholder="Optional remark" :disabled="loading" />
        </UiFormControl>
        <UiFormMessage />
      </UiFormItem>
    </FormField>

    <div class="flex justify-end gap-2">
      <UiButton type="submit" :disabled="loading">
        <UiSpinner v-if="loading" class="mr-2" />
        Save
      </UiButton>
    </div>
  </form>
</template>
