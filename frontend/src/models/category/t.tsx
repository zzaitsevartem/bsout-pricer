import { useState } from "react"
import { useCategories, useCategory, useCreateCategory } from "./hooks"
import { CategoryCreateRequest, categoryCreateRequestSchema } from "./schema"

import { useForm } 'react-hook-form'
import { zodResolver } from '@hookform/resolvers'

export const Rrr = () => {
    const query = useCreateCategory()

    const form = useForm({
        defaultValues: {
            name: '',
            slug: ''
        },
        resolver: zodResolver(categoryCreateRequestSchema)
    })

    const handlerCreate = (data: CategoryCreateRequest) => {
        query.mutate(data)
    }    

    return <>

        <label>Название</label>
        <input placeholder="..." {...form.register('name')} />
        <span>{form?.formState?.errors?.name}</span>

        <label>Slug</label>
        <input placeholder="..." {...form.register('slug')} />
        <span>{form?.formState?.errors?.slug}</span>
    
        <button onClick={form.handleSubmit(handlerCreate)}>создать</button>
    </>
}
