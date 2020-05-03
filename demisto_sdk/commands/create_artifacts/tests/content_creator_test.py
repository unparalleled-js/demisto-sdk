import filecmp
from tempfile import mkdtemp

from demisto_sdk.commands.common.git_tools import git_path
from demisto_sdk.commands.create_artifacts.content_creator import *


class TestContentCreator:
    def setup(self):
        tests_dir = f'{git_path()}/demisto_sdk/tests'
        self.scripts_full_path = os.path.join(tests_dir, 'test_files', 'content_repo_example', 'Scripts')
        self.integrations_full_path = os.path.join(tests_dir, 'test_files', 'content_repo_example', 'Integrations')
        self.TestPlaybooks_full_path = os.path.join(tests_dir, 'test_files', 'content_repo_example', 'TestPlaybooks')
        self.Packs_full_path = os.path.join(tests_dir, 'test_files', 'content_repo_example', 'Packs')
        self._bundle_dir = mkdtemp()
        self._test_dir = mkdtemp()
        self.content_repo = os.path.join(tests_dir, 'test_files', 'content_repo_example')

    def teardown(self):
        # delete all files in the content_bundle
        directories = [self._bundle_dir, self._test_dir]
        for directory in directories:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as err:
                    print('Failed to delete {}. Reason: {}'.format(file_path, err))

    def test_copy_dir_files(self):
        """
        Given
        - valid content dir, including Scripts, Integrations and TestPlaybooks sub-dirs
        When
        - copying the content folder to a content bundle(flatten files)
        Then
        - ensure files are being flatten correctly
        - ensure no !!omap are added(due to ordereddict yaml problems)
        """
        content_creator = ContentCreator(artifacts_path=self.content_repo, content_version='2.5.0',
                                         content_bundle_path=self._bundle_dir,
                                         test_bundle_path=self._test_dir,
                                         preserve_bundles=False)

        # test Scripts repo copy
        content_creator.copy_dir_files(self.scripts_full_path, content_creator.content_bundle)
        assert filecmp.cmp(f'{self.scripts_full_path}/script-Sleep.yml',
                           f'{self._bundle_dir}/script-Sleep.yml')

        # test Integrations repo copy
        content_creator.copy_dir_files(f'{self.integrations_full_path}/Securonix', content_creator.content_bundle)
        print(f'{self._bundle_dir}/Panorama.yml')
        assert filecmp.cmp(f'{self.integrations_full_path}/Securonix/Securonix_unified.yml',
                           f'{self._bundle_dir}/Securonix_unified.yml')

        # test TestPlaybooks repo copy
        content_creator.copy_dir_files(self.TestPlaybooks_full_path, content_creator.test_bundle)
        assert filecmp.cmp(f'{self.TestPlaybooks_full_path}/script-Sleep-for-testplaybook.yml',
                           f'{self._test_dir}/script-Sleep-for-testplaybook.yml')

    def test_copy_packs_content_to_packs_bundle(self):
        """
        Given
        - valid content dir, including Packs sub-dir
        When
        - copying the content folder to a content bundle(flatten files)
        Then
        - ensure files are being flatten correctly
        - ensure no !!omap are added(due to ordereddict yaml problems)
        - ensure TestPlaybooks without the playbook-* prefix are valid
        """
        content_creator = ContentCreator(artifacts_path=self.content_repo, content_version='2.5.0',
                                         content_bundle_path=self._bundle_dir,
                                         test_bundle_path=self._test_dir,
                                         preserve_bundles=False)
        content_creator.copy_packs_content_to_old_bundles([f'{self.Packs_full_path}/FeedAzure'])

        # test Packs repo, TestPlaybooks repo copy without playbook- prefix
        assert filecmp.cmp(f'{self.Packs_full_path}/FeedAzure/TestPlaybooks/FeedAzure_test.yml',
                           f'{self._test_dir}/playbook-FeedAzure_test.yml')
        assert filecmp.cmp(f'{self.Packs_full_path}/FeedAzure/TestPlaybooks/playbook-FeedAzure_test_copy_no_prefix.yml',
                           f'{self._test_dir}/playbook-FeedAzure_test_copy_no_prefix.yml')

        # test Packs repo, TestPlaybooks repo copy scripts and do not add them the playbook- prefix
        assert filecmp.cmp(f'{self.Packs_full_path}/FeedAzure/TestPlaybooks/just_a_test_script.yml',
                           f'{self._test_dir}/script-just_a_test_script.yml')
        assert filecmp.cmp(f'{self.Packs_full_path}/FeedAzure/TestPlaybooks/script-prefixed_automation.yml',
                           f'{self._test_dir}/script-prefixed_automation.yml')

    def test_copy_docs_files(self, mocker):
        """
        Given
        - valid packs and content bundle paths.
        When
        - copying the common docs files to content and packs bundle
        Then
        - ensure common docs files are copied to correct path.
        """
        mocker.patch('builtins.print')
        mocker.patch('os.mkdir')

        doc_files_paths = ('./Documentation/doc-CommonServer.json', './Documentation/doc-howto.json')
        mocker.patch('os.path.exists', side_effect=lambda p: p in doc_files_paths)

        copied_to_bundle = mocker.patch('shutil.copyfile')
        copied_to_packs = mocker.patch('shutil.copy')

        ContentCreator.copy_docs_files(content_bundle_path="dummy_bundle_path", packs_bundle_path="dummy_packs_path")

        for called_bundle_args in copied_to_bundle.call_args_list:
            destination_copy_path = called_bundle_args.args[1]
            assert destination_copy_path in (
                'dummy_bundle_path/doc-CommonServer.json', 'dummy_bundle_path/doc-howto.json')

        for called_packs_args in copied_to_packs.call_args_list:
            destination_copy_path = called_packs_args.args[1]
            assert destination_copy_path in ("dummy_packs_path/Base/Documentation/doc-CommonServer.json",
                                             "dummy_packs_path/Base/Documentation/doc-howto.json")
