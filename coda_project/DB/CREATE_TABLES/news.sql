

CREATE TABLE IF NOT EXISTS public.news
(
    id integer NOT NULL DEFAULT nextval('news_id_seq'::regclass),
    region_id integer,
    chapter_id integer,
    title character varying(255) COLLATE pg_catalog."default" NOT NULL,
    source character varying(255) COLLATE pg_catalog."default" NOT NULL,
    published_date timestamp without time zone NOT NULL,
    create_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    update_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    image_url character varying(500) COLLATE pg_catalog."default",
    content text COLLATE pg_catalog."default" NOT NULL,
    link character varying(500) COLLATE pg_catalog."default",
    is_event boolean NOT NULL,
    category character varying(100) COLLATE pg_catalog."default",
    CONSTRAINT news_pkey PRIMARY KEY (id),
    CONSTRAINT news_chapter_id_fkey FOREIGN KEY (chapter_id)
        REFERENCES public.chapter (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT news_region_id_fkey FOREIGN KEY (region_id)
        REFERENCES public.region (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.news
    OWNER to postgres;